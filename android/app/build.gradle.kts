import java.util.Properties

plugins { id("com.android.application") }

val repository = rootProject.projectDir
val localSettings = Properties().apply {
    val settingsFile = rootProject.file("local.properties")
    if (settingsFile.isFile) settingsFile.inputStream().use { load(it) }
}

// The player's own ROM for each game, from -Pmonoloco.romN or local.properties. A game without
// one is left out of the APK (it can still be imported as a core built on a PC).
fun romFor(game: Int): File? {
    val path = providers.gradleProperty("monoloco.rom$game").orNull ?: localSettings.getProperty("monoloco.rom$game")
    return path?.takeIf { it.isNotBlank() }?.let { repository.resolve(it) }
}
val roms = (1..3).associateWith { romFor(it) }.filterValues { it != null }.mapValues { it.value!! }
// CI: compile the three cores' runners even without ROMs (nothing is linked or packaged).
val checkCores = providers.gradleProperty("monoloco.checkCores").map { it.toBoolean() }.orElse(false).get()
val pythonCommand = providers.gradleProperty("monoloco.python").orElse("python3")
fun generatedDir(game: Int) = repository.resolve("upstream/game$game/generated/snesrecomp")

abstract class GeneratorServices @javax.inject.Inject constructor(
    val processes: org.gradle.process.ExecOperations
)
val generatorServices = objects.newInstance<GeneratorServices>()

val generateGames = tasks.register("generateGames") {
    group = "build"
    description = "Generate each game's C sources from the player's ROM (never committed)."
    for ((game, rom) in roms) {
        inputs.file(rom).withPropertyName("rom$game")
        inputs.dir(repository.resolve("upstream/game$game/recomp")).withPropertyName("cfg$game")
        outputs.dir(generatedDir(game)).withPropertyName("generated$game")
    }
    doLast {
        for ((game, rom) in roms) {
            generatorServices.processes.exec {
                workingDir(repository)
                commandLine(pythonCommand.get(), "tools/generate.py", "--game", "$game", "--rom", rom.absolutePath)
            }
        }
    }
}

val buildCommit = providers.exec {
    workingDir(repository)
    commandLine("git", "rev-parse", "HEAD")
}.standardOutput.asText.map { it.trim() }

// SDL's Java half must match the SDL2 the frontend links (android/SDL, same release).
val prepareSdlJava = tasks.register("prepareSdlJava") {
    val source = file("../SDL/android-project/app/src/main/java")
    val output = layout.buildDirectory.dir("generated/sdl-java")
    inputs.dir(source)
    outputs.dir(output)
    doLast {
        output.get().asFile.deleteRecursively()
        source.walkTopDown().filter { it.isFile && it.extension == "java" }.forEach { original ->
            val destination = output.get().asFile.resolve(original.relativeTo(source))
            destination.parentFile.mkdirs()
            var text = original.readText()
            if (original.name == "HIDDeviceManager.java") {
                // Android 14+ requires an explicit export flag on runtime receivers.
                val call = "mContext.registerReceiver(mUsbBroadcast, filter);"
                check(text.contains(call)) { "SDL USB receiver changed: review the Android patch" }
                text = text.replace(call, """
                    if (android.os.Build.VERSION.SDK_INT >= 33) {
                        mContext.registerReceiver(mUsbBroadcast, filter, android.content.Context.RECEIVER_NOT_EXPORTED);
                    } else {
                        mContext.registerReceiver(mUsbBroadcast, filter);
                    }
                """.trimIndent())
                text = text.replace("private void initializeUSB()", "@android.annotation.SuppressLint(\"UnspecifiedRegisterReceiverFlag\")\n    private void initializeUSB()")
            }
            destination.writeText(text)
        }
    }
}

android {
    namespace = "com.monolocosaga"
    compileSdk = 37
    ndkVersion = "30.0.16248370"
    buildFeatures { buildConfig = true }
    defaultConfig {
        applicationId = "com.monolocosaga"
        minSdk = 30
        targetSdk = 37
        // CI builds count up so every APK installs as an update (0.1.<run>).
        val runNumber = providers.environmentVariable("GITHUB_RUN_NUMBER").orNull?.toIntOrNull()
        versionCode = runNumber ?: 1
        versionName = "0.1.${runNumber ?: 0}"
        buildConfigField("String", "BUILD_COMMIT", "\"${buildCommit.get().take(12)}\"")
        buildConfigField("String", "BUILD_COMMIT_FULL", "\"${buildCommit.get()}\"")
        ndk { abiFilters += "arm64-v8a" }
        externalNativeBuild {
            cmake {
                arguments += listOf(
                    "-DANDROID_STL=c++_static",
                    "-DCMAKE_BUILD_TYPE=Release",
                    "-DMONOLOCO_CHECK_CORES=${if (checkCores) "ON" else "OFF"}")
                for (game in roms.keys) {
                    arguments += "-DMONOLOCO_GAME${game}_GEN_DIR=${generatedDir(game).absolutePath}"
                }
            }
        }
    }
    // A fixed key (MONOLOCO_KEYSTORE, a .jks path, plus MONOLOCO_KEYSTORE_PASSWORD) keeps every build
    // installable over the previous one; without it the debug key signs the APK.
    val stableKeystore = providers.environmentVariable("MONOLOCO_KEYSTORE").orNull
    signingConfigs {
        if (stableKeystore != null) {
            create("stable") {
                storeFile = file(stableKeystore)
                storePassword = providers.environmentVariable("MONOLOCO_KEYSTORE_PASSWORD").get()
                keyAlias = "monolocosaga"
                keyPassword = providers.environmentVariable("MONOLOCO_KEYSTORE_PASSWORD").get()
            }
        }
    }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.findByName("stable") ?: signingConfigs.getByName("debug")
        }
    }
    externalNativeBuild {
        cmake {
            path = file("../native/CMakeLists.txt")
            version = "4.1.2"
        }
    }
    // GameActivity checks for the bundled cores on disk, so native libraries are extracted.
    packaging { jniLibs { useLegacyPackaging = true } }
    sourceSets["main"].java.directories.add(layout.buildDirectory.dir("generated/sdl-java").get().asFile.path)
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

tasks.named("preBuild") { dependsOn(prepareSdlJava) }

// CMake configuration globs the generated sources, so generation must finish before it.
tasks.configureEach {
    if (name.startsWith("configureCMake") || name.startsWith("buildCMake") || name.startsWith("externalNativeBuild")) {
        dependsOn(generateGames)
    }
}
