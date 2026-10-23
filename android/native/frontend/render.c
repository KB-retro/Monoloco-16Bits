// OpenGL ES 3: one textured quad, one shader with the filter and effect as
// uniforms. The core writes BGRA bytes; the shader swaps them back.
#include "render.h"
#include "frontend.h"

#include <GLES3/gl3.h>
#include <android/log.h>
#include <math.h>
#include <stddef.h>

#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "Monoloco", __VA_ARGS__)

static GLuint s_program, s_texture, s_vao, s_vbo;
static GLint s_u_texture, s_u_source, s_u_output, s_u_filter, s_u_effect;
static int s_tex_width, s_tex_height;
static int s_frame_width = 256, s_frame_height = 224;
static bool s_have_frame;

static const char *kVertex =
    "#version 300 es\n"
    "layout(location = 0) in vec2 aPosition;\n"
    "layout(location = 1) in vec2 aUv;\n"
    "out vec2 vUv;\n"
    "void main() { vUv = aUv; gl_Position = vec4(aPosition, 0.0, 1.0); }\n";

// Filters: 0 nearest, 1 linear, 2 sharp bilinear (pixel interiors stay flat,
// only the borders blend). Effects: 0 none, 1 scanlines, 2 CRT (scanlines,
// aperture mask and a soft vignette).
static const char *kFragment =
    "#version 300 es\n"
    "precision highp float;\n"
    "in vec2 vUv;\n"
    "out vec4 fragColor;\n"
    "uniform sampler2D uTexture;\n"
    "uniform vec2 uSource;\n"
    "uniform vec2 uOutput;\n"
    "uniform int uFilter;\n"
    "uniform int uEffect;\n"
    "void main() {\n"
    "  vec2 texel = vUv * uSource;\n"
    "  vec2 uv = vUv;\n"
    "  if (uFilter == 0) {\n"
    "    uv = (floor(texel) + 0.5) / uSource;\n"
    "  } else if (uFilter == 2) {\n"
    "    vec2 scale = max(uOutput / uSource, vec2(1.0));\n"
    "    vec2 region = 0.5 - 0.5 / scale;\n"
    "    vec2 center = fract(texel) - 0.5;\n"
    "    vec2 f = (center - clamp(center, -region, region)) * scale + 0.5;\n"
    "    uv = (floor(texel) + f) / uSource;\n"
    "  }\n"
    "  vec3 color = texture(uTexture, uv).bgr;\n"
    "  if (uEffect >= 1) {\n"
    "    float line = 0.5 + 0.5 * cos(6.2831853 * (fract(texel.y) - 0.5));\n"
    "    float strength = uEffect == 1 ? 0.35 : 0.45;\n"
    "    color *= mix(1.0 - strength, 1.0, line);\n"
    "  }\n"
    "  if (uEffect == 2) {\n"
    "    float column = mod(gl_FragCoord.x, 3.0);\n"
    "    vec3 mask = column < 1.0 ? vec3(1.0, 0.82, 0.82)\n"
    "              : column < 2.0 ? vec3(0.82, 1.0, 0.82) : vec3(0.82, 0.82, 1.0);\n"
    "    color *= mask * 1.22;\n"
    "    vec2 edge = vUv * (1.0 - vUv);\n"
    "    color *= clamp(pow(edge.x * edge.y * 16.0, 0.12), 0.0, 1.0);\n"
    "  }\n"
    "  fragColor = vec4(color, 1.0);\n"
    "}\n";

static GLuint Compile(GLenum type, const char *source) {
  GLuint shader = glCreateShader(type);
  glShaderSource(shader, 1, &source, NULL);
  glCompileShader(shader);
  GLint ok = 0;
  glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
  if (!ok) {
    char log[1024];
    glGetShaderInfoLog(shader, sizeof log, NULL, log);
    LOGE("shader: %s", log);
    glDeleteShader(shader);
    return 0;
  }
  return shader;
}

bool RenderInit(void) {
  GLuint vertex = Compile(GL_VERTEX_SHADER, kVertex);
  GLuint fragment = Compile(GL_FRAGMENT_SHADER, kFragment);
  if (!vertex || !fragment) return false;
  s_program = glCreateProgram();
  glAttachShader(s_program, vertex);
  glAttachShader(s_program, fragment);
  glLinkProgram(s_program);
  glDeleteShader(vertex);
  glDeleteShader(fragment);
  GLint ok = 0;
  glGetProgramiv(s_program, GL_LINK_STATUS, &ok);
  if (!ok) {
    LOGE("shader program did not link");
    return false;
  }
  s_u_texture = glGetUniformLocation(s_program, "uTexture");
  s_u_source = glGetUniformLocation(s_program, "uSource");
  s_u_output = glGetUniformLocation(s_program, "uOutput");
  s_u_filter = glGetUniformLocation(s_program, "uFilter");
  s_u_effect = glGetUniformLocation(s_program, "uEffect");

  glGenVertexArrays(1, &s_vao);
  glGenBuffers(1, &s_vbo);
  glBindVertexArray(s_vao);
  glBindBuffer(GL_ARRAY_BUFFER, s_vbo);
  glBufferData(GL_ARRAY_BUFFER, 16 * sizeof(float), NULL, GL_DYNAMIC_DRAW);
  glEnableVertexAttribArray(0);
  glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void *)0);
  glEnableVertexAttribArray(1);
  glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float),
                        (void *)(2 * sizeof(float)));
  glBindVertexArray(0);

  glGenTextures(1, &s_texture);
  s_tex_width = s_tex_height = 0;
  s_have_frame = false;
  return true;
}

void RenderShutdown(void) {
  if (s_texture) glDeleteTextures(1, &s_texture);
  if (s_vbo) glDeleteBuffers(1, &s_vbo);
  if (s_vao) glDeleteVertexArrays(1, &s_vao);
  if (s_program) glDeleteProgram(s_program);
  s_texture = s_vbo = s_vao = s_program = 0;
}

void RenderUpload(const uint8_t *pixels, int width, int height) {
  if (!s_texture || !pixels || width <= 0 || height <= 0) return;
  glBindTexture(GL_TEXTURE_2D, s_texture);
  glPixelStorei(GL_UNPACK_ALIGNMENT, 4);
  // Exactly the frame's size, so linear filtering never reads past its edge.
  if (width != s_tex_width || height != s_tex_height) {
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA,
                 GL_UNSIGNED_BYTE, pixels);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    s_tex_width = width;
    s_tex_height = height;
  } else {
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA,
                    GL_UNSIGNED_BYTE, pixels);
  }
  s_frame_width = width;
  s_frame_height = height;
  s_have_frame = true;
}

void RenderDraw(int drawable_width, int drawable_height, int filter, int effect,
                int scale, bool original_pixels) {
  glViewport(0, 0, drawable_width, drawable_height);
  glClearColor(0, 0, 0, 1);
  glClear(GL_COLOR_BUFFER_BIT);
  if (!s_have_frame || drawable_width <= 0 || drawable_height <= 0) return;

  // The console drew 8:7 pixels: 256 columns filled a 4:3 picture.
  float pixel_aspect = original_pixels ? 8.0f / 7.0f : 1.0f;
  float content_width = s_frame_width * pixel_aspect;
  float content_height = (float)s_frame_height;
  float width, height;
  if (scale == kScaleStretch) {
    width = (float)drawable_width;
    height = (float)drawable_height;
  } else {
    float fit = fminf(drawable_width / content_width, drawable_height / content_height);
    if (scale == kScaleInteger && fit >= 1.0f) fit = floorf(fit);
    width = content_width * fit;
    height = content_height * fit;
  }
  float x = width / drawable_width;  // half extents in clip space
  float y = height / drawable_height;
  const float quad[16] = {
      -x, -y, 0.0f, 1.0f,  x, -y, 1.0f, 1.0f,
      -x,  y, 0.0f, 0.0f,  x,  y, 1.0f, 0.0f,
  };
  glUseProgram(s_program);
  glBindVertexArray(s_vao);
  glBindBuffer(GL_ARRAY_BUFFER, s_vbo);
  glBufferSubData(GL_ARRAY_BUFFER, 0, sizeof quad, quad);
  glActiveTexture(GL_TEXTURE0);
  glBindTexture(GL_TEXTURE_2D, s_texture);
  GLint sampling = filter == kFilterNearest ? GL_NEAREST : GL_LINEAR;
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, sampling);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, sampling);
  glUniform1i(s_u_texture, 0);
  glUniform2f(s_u_source, (float)s_frame_width, (float)s_frame_height);
  glUniform2f(s_u_output, width, height);
  glUniform1i(s_u_filter, filter);
  glUniform1i(s_u_effect, effect);
  glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
  glBindVertexArray(0);
}
