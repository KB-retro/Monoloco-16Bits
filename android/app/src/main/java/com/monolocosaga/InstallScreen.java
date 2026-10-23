package com.monolocosaga;

import android.app.Activity;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.util.DisplayMetrics;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

/** "Installing..." over the launcher while the folder's files are copied: logo, bar and percentage. */
final class InstallScreen {
    private final ViewGroup parent;
    private final FrameLayout screen;
    private final ProgressBar bar;
    private final TextView percent;
    private float shown; // the bar never goes back

    private InstallScreen(Activity activity, ViewGroup parent) {
        this.parent = parent;
        screen = new FrameLayout(activity);
        screen.setBackgroundColor(Color.BLACK);
        screen.setClickable(true); // nothing reaches the launcher underneath
        ImageView backdrop = new ImageView(activity);
        backdrop.setImageResource(R.drawable.launcher_backdrop);
        backdrop.setScaleType(ImageView.ScaleType.CENTER_CROP);
        backdrop.setColorFilter(0x99000000);
        screen.addView(backdrop, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout column = new LinearLayout(activity);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setGravity(Gravity.CENTER);
        DisplayMetrics metrics = activity.getResources().getDisplayMetrics();
        ImageView logo = new ImageView(activity);
        logo.setImageResource(R.drawable.launcher_logo);
        logo.setAdjustViewBounds(true);
        column.addView(logo, new LinearLayout.LayoutParams(-2, metrics.heightPixels * 28 / 100));
        TextView title = new TextView(activity);
        title.setText(R.string.install_title);
        title.setTextColor(Color.WHITE);
        title.setTextSize(22);
        title.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD_ITALIC));
        title.setPadding(0, metrics.heightPixels / 30, 0, metrics.heightPixels / 60);
        title.setGravity(Gravity.CENTER);
        column.addView(title);
        bar = new ProgressBar(activity, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(1000);
        bar.setProgressTintList(ColorStateList.valueOf(0xFF32FFE6));
        column.addView(bar, new LinearLayout.LayoutParams(metrics.widthPixels * 55 / 100, -2));
        percent = new TextView(activity);
        percent.setTextColor(0xFFB8F5E6);
        percent.setTextSize(14);
        percent.setPadding(0, metrics.heightPixels / 60, 0, 0);
        percent.setGravity(Gravity.CENTER);
        column.addView(percent);
        screen.addView(column, new FrameLayout.LayoutParams(-1, -1));
        setProgress(0);
    }

    static InstallScreen show(Activity activity, ViewGroup parent) {
        InstallScreen install = new InstallScreen(activity, parent);
        parent.addView(install.screen, new ViewGroup.LayoutParams(-1, -1));
        return install;
    }

    void setProgress(float fraction) {
        shown = Math.max(shown, Math.max(0f, Math.min(1f, fraction)));
        bar.setProgress(Math.round(shown * 1000));
        percent.setText(screen.getContext().getString(R.string.install_percent, Math.round(shown * 100)));
    }

    void dismiss() {
        parent.removeView(screen);
    }
}
