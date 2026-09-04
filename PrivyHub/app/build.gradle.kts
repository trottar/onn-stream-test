plugins {
    alias(libs.plugins.android.application)
}


android {

    namespace = "com.safeiot.privyhub"


    compileSdk {
        version = release(37)
    }


    defaultConfig {

        applicationId = "com.safeiot.privyhub"

        minSdk = 24

        targetSdk = 37

        versionCode = 1

        versionName = "1.0"

        testInstrumentationRunner =
            "androidx.test.runner.AndroidJUnitRunner"
    }


    buildTypes {

        release {

            optimization {
                enable = false
            }
        }
    }


    compileOptions {

        sourceCompatibility =
            JavaVersion.VERSION_11

        targetCompatibility =
            JavaVersion.VERSION_11
    }
}


dependencies {

    implementation(
        "androidx.media3:media3-exoplayer:1.11.0"
    )

    implementation(
        "androidx.media3:media3-exoplayer-hls:1.11.0"
    )

    implementation(
        "androidx.media3:media3-ui:1.11.0"
    )

    implementation(
        libs.androidx.activity.ktx
    )

    implementation(
        libs.androidx.appcompat
    )

    implementation(
        libs.androidx.constraintlayout
    )

    implementation(
        libs.androidx.core.ktx
    )

    implementation(
        libs.material
    )


    testImplementation(
        libs.junit
    )


    androidTestImplementation(
        libs.androidx.espresso.core
    )

    androidTestImplementation(
        libs.androidx.junit
    )
}