package com.monolocosaga;

/**
 * The native frontend (android/native/frontend/bridge.c). Setters take effect on the game's next
 * frame; the state calls block until the game thread ran them (at most a few seconds).
 */
final class GameBridge {
    static final int STATE_LOADING = 0, STATE_RUNNING = 1, STATE_FAILED = 2;

    private GameBridge() { }

    /** While open, the game holds still. */
    static native void nativeSetMenuOpen(boolean open);

    /** Player 1's touch pad, in the runners' packed bits. */
    static native void nativeSetTouch(int buttons);

    /** Frames presented so far, for the FPS counter. */
    static native int nativeFrames();

    static native int nativeState();

    /** Why the game could not start or stopped; "" when it did not. */
    static native String nativeError();

    static native void nativeSetVideo(int filter, int effect, int scale, boolean originalPixels);

    /** 0 original 4:3, 1 16:10, 2 16:9. */
    static native void nativeSetAspect(int aspect);

    static native void nativeSetVolume(int percent);

    static native boolean nativeSaveState(String path);

    static native boolean nativeLoadState(String path);

    /** Writes the battery save now. */
    static native boolean nativeFlush();
}
