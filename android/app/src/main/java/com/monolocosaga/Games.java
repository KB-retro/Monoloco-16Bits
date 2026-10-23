package com.monolocosaga;

import android.content.Context;
import java.io.File;

/**
 * The three games: where their ROM, saves and core live. Game n (1..3) keeps everything in
 * {@code <app folder>/game<n>/}; the core is the APK's own or one imported into the private files.
 */
final class Games {
    static final int COUNT = 3;
    static final long ROM_SIZE = 4L * 1024 * 1024;
    /** The headerless USA ROMs each upstream project was generated from. */
    static final String[] SHA256 = {
        "fa8cacf5bbfc39ee6bbaa557adf89133d60d42f6cf9e1db30d5a36a469f74d15",
        "35421a9af9dd011b40b91f792192af9f99c93201d8d394026bdfb42cbf2d8633",
        "2277a2d8dddb01fe5cb0ae9a0fa225d42b3a11adccaeafa18e3c339b3794a32b",
    };
    static final int[] TITLES = {R.string.game1_title, R.string.game2_title, R.string.game3_title};
    static final int[] SUBTITLES = {R.string.game1_subtitle, R.string.game2_subtitle, R.string.game3_subtitle};
    static final int[] LOGOS = {R.drawable.game1_logo, R.drawable.game2_logo, R.drawable.game3_logo};

    private Games() { }

    /** The folder the app treats as its data directory (Android/data/com.monolocosaga/files). */
    static File appDir(Context context) {
        File external = context.getExternalFilesDir(null);
        return external != null ? external : context.getFilesDir();
    }

    static File dir(Context context, int game) { return new File(appDir(context), "game" + game); }

    static File rom(Context context, int game) { return new File(dir(context, game), "rom.sfc"); }

    static File states(Context context, int game) { return new File(dir(context, game), "states"); }

    static File lastError(Context context, int game) { return new File(dir(context, game), "last_error.txt"); }

    static String coreName(int game) { return "libmonoloco_game" + game + ".so"; }

    /** Imported cores must be in private storage: shared storage cannot hold executable code. */
    static File importedCore(Context context, int game) {
        return new File(new File(context.getFilesDir(), "cores"), coreName(game));
    }

    /** The APK's own core when it has one, otherwise an imported one; null when neither. */
    static File core(Context context, int game) {
        File bundled = new File(context.getApplicationInfo().nativeLibraryDir, coreName(game));
        if (bundled.isFile()) return bundled;
        File imported = importedCore(context, game);
        return imported.isFile() ? imported : null;
    }

    static boolean hasRom(Context context, int game) { return rom(context, game).isFile(); }

    static boolean ready(Context context, int game) { return hasRom(context, game) && core(context, game) != null; }

    static int selected(Context context) {
        int game = context.getSharedPreferences("game", Context.MODE_PRIVATE).getInt("selected_game", 1);
        return game >= 1 && game <= COUNT ? game : 1;
    }

    static void select(Context context, int game) {
        context.getSharedPreferences("game", Context.MODE_PRIVATE).edit().putInt("selected_game", game).apply();
    }
}
