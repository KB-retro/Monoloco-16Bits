package com.monolocosaga;

import android.content.Context;
import android.content.SharedPreferences;

/** Preferences shared by the launcher, the quick menu and every game. */
final class LauncherSettings {
    // Picture: format 0 automatic, 1 original 4:3, 2 16:10, 3 16:9.
    static final String FORMAT = "format", SCALE = "scale", SQUARE_PIXELS = "square_pixels",
        FILTER = "filter", EFFECT = "effect", VOLUME = "volume", FPS = "fps", SLOT = "slot",
        FAST_CORES = "fast_cores", HD_LEVEL = "hd_level";
    /** Reconstruct, the HD upscaler, unless the player picked another filter. */
    static final int DEFAULT_FILTER = 2;

    private LauncherSettings() { }

    static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences("game", Context.MODE_PRIVATE);
    }

    static boolean autoStart(Context context) { return prefs(context).getBoolean("auto_start", false); }

    static void setAutoStart(Context context, boolean value) {
        prefs(context).edit().putBoolean("auto_start", value).apply();
    }

    static int get(Context context, String key, int fallback) { return prefs(context).getInt(key, fallback); }

    static void set(Context context, String key, int value) { prefs(context).edit().putInt(key, value).apply(); }

    /** The core's aspect (0 4:3, 1 16:10, 2 16:9) for the format setting on this screen. */
    static int aspect(android.app.Activity activity) {
        int format = get(activity, FORMAT, 0);
        if (format == 1) return 0;
        if (format == 2) return 1;
        if (format == 3) return 2;
        android.graphics.Rect bounds = activity.getWindowManager().getMaximumWindowMetrics().getBounds();
        float ratio = (float) Math.max(bounds.width(), bounds.height())
            / Math.max(1, Math.min(bounds.width(), bounds.height()));
        if (ratio >= 1.7f) return 2;
        if (ratio >= 1.55f) return 1;
        return 0;
    }

    /** Sends every picture and sound setting to the game. */
    static void apply(android.app.Activity activity) {
        try {
            GameBridge.nativeSetVideo(get(activity, FILTER, DEFAULT_FILTER), get(activity, EFFECT, 0),
                get(activity, SCALE, 0), get(activity, SQUARE_PIXELS, 0) == 0);
            GameBridge.nativeSetAspect(aspect(activity));
            GameBridge.nativeSetVolume(get(activity, VOLUME, 100));
            GameBridge.nativeSetHdLevel(get(activity, HD_LEVEL, 1));
            GameBridge.nativeSetFastCores(get(activity, FAST_CORES, 1) == 1);
        } catch (UnsatisfiedLinkError error) {
            android.util.Log.w("Monoloco", "Game library not loaded", error);
        }
    }
}
