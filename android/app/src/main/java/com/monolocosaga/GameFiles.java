package com.monolocosaga;

import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Imports what the player's folder holds: the three ROMs, found by size and SHA-256 whatever their
 * names (a 512-byte copier header is dropped), and cores built on a PC (libmonoloco_gameN.so).
 * The folder and one level of subfolders are searched.
 */
final class GameFiles {
    private static final int HEADER = 512;
    private static final long MAX_CORE = 512L * 1024 * 1024;

    interface Progress {
        /** fraction 0..1 of all bytes to copy. */
        void update(float fraction);
    }

    /** What the scan found. */
    static final class Scan {
        final boolean[] roms = new boolean[Games.COUNT + 1];
        final boolean[] cores = new boolean[Games.COUNT + 1];
        int unknownRoms;
        int badCores;

        boolean any() {
            for (int i = 1; i <= Games.COUNT; i++) if (roms[i] || cores[i]) return true;
            return false;
        }
    }

    private static final class Candidate {
        Uri uri;
        String name;
        long size;
        boolean core;
        int game;
    }

    private GameFiles() { }

    static Scan importFrom(Context context, Uri tree, Progress progress) throws IOException {
        ContentResolver resolver = context.getContentResolver();
        List<Candidate> found = new ArrayList<>();
        String root = DocumentsContract.getTreeDocumentId(tree);
        list(resolver, tree, root, found, 1);
        long total = 0;
        for (Candidate candidate : found) total += candidate.size;
        Scan scan = new Scan();
        long[] done = {0};
        for (Candidate candidate : found) {
            if (candidate.core) {
                if (scan.cores[candidate.game]) continue;
                if (copyCore(context, candidate, progress, done, total)) scan.cores[candidate.game] = true;
                else scan.badCores++;
            } else {
                int game = copyRom(context, candidate, progress, done, total);
                if (game > 0) scan.roms[game] = true;
                else scan.unknownRoms++;
            }
        }
        progress.update(1);
        return scan;
    }

    private static void list(ContentResolver resolver, Uri tree, String parent, List<Candidate> into, int depth)
            throws IOException {
        Uri children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, parent);
        String[] columns = {DocumentsContract.Document.COLUMN_DOCUMENT_ID,
            DocumentsContract.Document.COLUMN_DISPLAY_NAME, DocumentsContract.Document.COLUMN_SIZE,
            DocumentsContract.Document.COLUMN_MIME_TYPE};
        List<String> folders = new ArrayList<>();
        try (Cursor cursor = resolver.query(children, columns, null, null, null)) {
            if (cursor == null) throw new IOException("Cannot list the folder");
            while (cursor.moveToNext()) {
                String id = cursor.getString(0);
                String name = cursor.getString(1) != null ? cursor.getString(1) : "";
                if (DocumentsContract.Document.MIME_TYPE_DIR.equals(cursor.getString(3))) {
                    folders.add(id);
                    continue;
                }
                long size = cursor.getLong(2);
                Candidate candidate = new Candidate();
                candidate.uri = DocumentsContract.buildDocumentUriUsingTree(tree, id);
                candidate.name = name;
                candidate.size = size;
                String lower = name.toLowerCase(Locale.ROOT);
                if (size == Games.ROM_SIZE || size == Games.ROM_SIZE + HEADER) {
                    into.add(candidate);
                } else if (lower.endsWith(".so") && size > 0 && size < MAX_CORE) {
                    for (int game = 1; game <= Games.COUNT; game++) {
                        if (lower.contains("game" + game)) {
                            candidate.core = true;
                            candidate.game = game;
                            into.add(candidate);
                            break;
                        }
                    }
                }
            }
        }
        if (depth > 0) for (String folder : folders) list(resolver, tree, folder, into, depth - 1);
    }

    /** Returns the game the ROM belongs to, or 0 when it is not one of the three. */
    private static int copyRom(Context context, Candidate rom, Progress progress, long[] done, long total)
            throws IOException {
        File temporary = new File(Games.appDir(context), ".import.tmp");
        File parent = temporary.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot create " + parent);
        String sha = copy(context, rom.uri, temporary, rom.size == Games.ROM_SIZE + HEADER ? HEADER : 0,
                progress, done, total);
        for (int game = 1; game <= Games.COUNT; game++) {
            if (!Games.SHA256[game - 1].equals(sha)) continue;
            File destination = Games.rom(context, game);
            install(temporary, destination);
            return game;
        }
        temporary.delete();
        return 0;
    }

    private static boolean copyCore(Context context, Candidate core, Progress progress, long[] done, long total)
            throws IOException {
        File destination = Games.importedCore(context, core.game);
        File temporary = new File(destination.getPath() + ".tmp");
        File parent = destination.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot create " + parent);
        copy(context, core.uri, temporary, 0, progress, done, total);
        if (!isArm64Elf(temporary)) {
            temporary.delete();
            return false;
        }
        if (destination.exists()) {
            destination.setWritable(true);
            if (!destination.delete()) throw new IOException("Cannot replace " + destination);
        }
        if (!temporary.renameTo(destination)) throw new IOException("Cannot write " + destination);
        // Android 14+ only loads native code from read-only files.
        destination.setReadOnly();
        return true;
    }

    private static boolean isArm64Elf(File file) {
        byte[] header = new byte[20];
        try (InputStream input = new java.io.FileInputStream(file)) {
            if (input.read(header) != header.length) return false;
        } catch (IOException exception) {
            return false;
        }
        // ELF, 64-bit, little-endian, shared object, machine 183 (AArch64).
        return header[0] == 0x7F && header[1] == 'E' && header[2] == 'L' && header[3] == 'F'
            && header[4] == 2 && header[5] == 1 && header[16] == 3 && (header[18] & 255) == 183;
    }

    private static void install(File temporary, File destination) throws IOException {
        File parent = destination.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot create " + parent);
        if (destination.exists() && !destination.delete()) throw new IOException("Cannot replace " + destination);
        if (!temporary.renameTo(destination)) throw new IOException("Cannot write " + destination);
    }

    /** Copies a document, skipping its first bytes, and returns the SHA-256 of what was written. */
    private static String copy(Context context, Uri document, File destination, int skip, Progress progress,
            long[] done, long total) throws IOException {
        MessageDigest digest;
        try {
            digest = MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException exception) {
            throw new IOException(exception);
        }
        byte[] buffer = new byte[1 << 16];
        long lastUpdate = 0;
        try (InputStream input = context.getContentResolver().openInputStream(document);
             OutputStream output = new FileOutputStream(destination)) {
            if (input == null) throw new IOException("Cannot open " + document);
            long skipped = 0;
            while (skipped < skip) {
                long n = input.skip(skip - skipped);
                if (n <= 0) throw new IOException("Short file");
                skipped += n;
            }
            done[0] += skip;
            int count;
            while ((count = input.read(buffer)) > 0) {
                digest.update(buffer, 0, count);
                output.write(buffer, 0, count);
                done[0] += count;
                long now = android.os.SystemClock.elapsedRealtime();
                if (total > 0 && now - lastUpdate > 100) {
                    lastUpdate = now;
                    progress.update(Math.min(1f, (float) done[0] / total));
                }
            }
        }
        StringBuilder hex = new StringBuilder();
        for (byte b : digest.digest()) hex.append(String.format(Locale.ROOT, "%02x", b & 255));
        return hex.toString();
    }
}
