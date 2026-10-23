package com.monolocosaga;

import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.LightingColorFilter;
import android.graphics.Paint;
import android.graphics.RectF;
import java.util.HashMap;
import java.util.Map;

/** Cached artwork for every TouchLayout button id (same neon style as NFSU-X and G-Zero 64). */
final class TouchControlArtwork {
    private static final String[] IDS = {
        "dpad", "b", "a", "y", "x", "l", "r", "select", "start"
    };
    private static final int[] RESOURCES = {
        R.drawable.touch_dpad, R.drawable.touch_b, R.drawable.touch_a, R.drawable.touch_y,
        R.drawable.touch_x, R.drawable.touch_l, R.drawable.touch_r, R.drawable.touch_select,
        R.drawable.touch_start
    };

    private final Map<String, Bitmap> images = new HashMap<>();
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final Paint glow = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF destination = new RectF();
    private final LightingColorFilter pressed = new LightingColorFilter(0xFFFFFFFF, 0x00202020);

    TouchControlArtwork(Resources resources) {
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inScaled = false;
        for (int i = 0; i < IDS.length; i++) {
            images.put(IDS[i], BitmapFactory.decodeResource(resources, RESOURCES[i], options));
        }
        glow.setColor(0x7032FFE6);
    }

    void draw(Canvas canvas, String id, RectF bounds, boolean down, int alpha) {
        Bitmap image = images.get(id);
        if (image == null) return;
        float scale = Math.min(bounds.width() / image.getWidth(), bounds.height() / image.getHeight());
        float halfWidth = image.getWidth() * scale / 2;
        float halfHeight = image.getHeight() * scale / 2;
        destination.set(bounds.centerX() - halfWidth, bounds.centerY() - halfHeight,
                bounds.centerX() + halfWidth, bounds.centerY() + halfHeight);
        paint.setAlpha(down ? 255 : alpha);
        paint.setColorFilter(down ? pressed : null);
        canvas.drawBitmap(image, null, destination, paint);
    }

    /** Lights the pressed arms of the cross: dx and dy are -1, 0 or 1 (y grows downwards). */
    void drawDpadArms(Canvas canvas, RectF bounds, int dx, int dy) {
        float radius = Math.min(bounds.width(), bounds.height()) * 0.15f;
        float reach = Math.min(bounds.width(), bounds.height()) * 0.27f;
        if (dx != 0) canvas.drawCircle(bounds.centerX() + dx * reach, bounds.centerY(), radius, glow);
        if (dy != 0) canvas.drawCircle(bounds.centerX(), bounds.centerY() + dy * reach, radius, glow);
    }
}
