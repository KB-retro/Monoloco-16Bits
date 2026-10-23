package com.monolocosaga;

import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.util.Log;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/** Zips the app's own log and the games' error notes (no game data) into a file the player picked. */
final class DiagnosticLog {
    private DiagnosticLog() { }

    static boolean save(Context context, Uri target) {
        try (OutputStream raw = context.getContentResolver().openOutputStream(target, "w");
             ZipOutputStream zip = new ZipOutputStream(raw)) {
            if (raw == null) return false;
            StringBuilder device = new StringBuilder();
            device.append("Monoloco Saga ").append(BuildConfig.VERSION_NAME)
                .append(" (").append(BuildConfig.BUILD_COMMIT).append(")\n")
                .append(Build.MANUFACTURER).append(' ').append(Build.MODEL)
                .append(", Android ").append(Build.VERSION.RELEASE)
                .append(" (API ").append(Build.VERSION.SDK_INT).append("), ").append(Build.HARDWARE).append('\n');
            for (int game = 1; game <= Games.COUNT; game++) {
                File core = Games.core(context, game);
                device.append("game").append(game).append(": rom=").append(Games.hasRom(context, game))
                    .append(" core=").append(core != null ? core.getName() + " " + core.length() : "none").append('\n');
            }
            entry(zip, "device.txt", device.toString().getBytes(StandardCharsets.UTF_8));
            // An app may read its own log lines.
            try {
                Process process = new ProcessBuilder("logcat", "-d", "-t", "4000").redirectErrorStream(true).start();
                try (InputStream input = process.getInputStream()) {
                    entry(zip, "logcat.txt", readAll(input, 8 << 20));
                }
            } catch (IOException exception) {
                Log.w("Monoloco", "No logcat", exception);
            }
            return true;
        } catch (IOException | RuntimeException exception) {
            Log.e("Monoloco", "Cannot save the log", exception);
            return false;
        }
    }

    private static void entry(ZipOutputStream zip, String name, byte[] data) throws IOException {
        zip.putNextEntry(new ZipEntry(name));
        zip.write(data);
        zip.closeEntry();
    }

    private static byte[] readAll(InputStream input, int limit) throws IOException {
        java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
        byte[] buffer = new byte[1 << 16];
        int count;
        while ((count = input.read(buffer)) > 0 && bytes.size() < limit) bytes.write(buffer, 0, count);
        return bytes.toByteArray();
    }
}
