<div align="center">

# Iconic (ES version)

![System Carousel Demo](_preview/systems-carousel-animation.gif)

**Iconic** is a theme for [EmulationStation](https://github.com/batocera-linux/batocera-emulationstation) (Batocera variant), based on [the ES-DE version](https://github.com/Siddy212/iconic-es-de) created by [@Siddy212](https://github.com/Siddy212).

</div>


## Preview

| Light Mode | Dark Mode|
| :--: | :--: |
| ![System View Light](_preview/systems-view-light-1.jpg) | ![System View Light](_preview/systems-view-dark-1.jpg) |
| ![Grid View Light](_preview/grid-view-light.jpg) | ![List View Dark](_preview/list-view-dark.jpg) |
| ![List View Light](_preview/list-view-light.jpg) | ![Basic View Dark](_preview/basic-view-dark.jpg) |


## Installation

If your version of EmulationStation supports it, you can install this theme using [the integrated downloader](https://wiki.batocera.org/themes#emulationstation_themes) from the main menu under `Updates & Downloads > Theme`.

Otherwise, you can [download this theme](https://github.com/Delgan/iconic-es/archive/refs/heads/main.zip) and uncompress it the appropriate "themes" folder of your distribution.

If you find any bugs or have suggestions for improvements, please feel free to [open an issue](https://github.com/Delgan/iconic-es/issues/new/choose).


## Configuration

The following options can be changed directly from the main menu under `User Interface Settings > Theme Configuration`

| Setting | Description | Options |
| -- | -- | -- |
| Aspect Ratio | Enables you to select the correct aspect ratio for your screen. This will automatically set itself so you should not need to change it but if the theme layout looks odd or spacing looks incorrect you can use this setting to make sure the aspect ratio matches your screen. | `Automatic`, `16:9`, `16:10`, `4:3`, `3:2`, `1:1` |
| Color Scheme | Sets the color scheme that is used for the theme. | `Light`, `Dark` |
| Game Media Type | Selects the desired type of image displayed above game details. | `Boxart`, `Image`, `Marquee`, `Mix` |
| Play Video Previews of Games | Toggles the video previews above game details (if available). | `Yes`, `No` |
| Show Game Titles in Grid | Toggles the display of game titles in the grid view. | `No`, `Yes` |
| Metadata Source | Selects the primary source of metadata (name, release year, etc.) to associate with each systems. | `Theme`, `EmulationStation` |
| Smooth Resize | Toggles the use of smooth resizing for images. Disabling this may lead to better looking images, but it requires the VRAM optimizations to be disabled in the settings as well. | `Yes`, `No` |
| Distribution | Used to define which folder to look in for theme customization files (see below). | `None`, `Batocera/Knulli`, `RetroBat`, `ROCKNIX` |

## Customization

This theme allows customizations to artwork without the need to edit the source XML. This enables you to change the look of the theme and still retain any changes when the root theme is updated.

### Start Here

- Make sure the `Distribution` setting is set to the correct value for your current OS (e.g. Batocera/Knulli, RetroBat or RockNIX)
- This value determines the folder where you will add your customizations:
    - Batocera/Knulli = `/userdata/theme-customizations/iconic/`
    - RockNIX = `/roms/_userdata/theme-customizations/iconic/`
    - Retrobat = `C:\RetroBat\emulationstation\.emulationstation\theme-customizations\iconic\`
- Create the folders that match your distribution.
- Within the `iconic` folder, create two additional subfolders named `backgrounds` and `overlays`.

### Backgrounds

The artwork used on the system view can be customized with your own images.

* Copy your custom background images to the `backgrounds` folder previously created.
* The images must be of 1920x1080 resolution.
* They should be named either (in order of precedence):
    - `${system.theme}.webp`
    - `${system.theme}.png`
* The `${system.theme}` variable corresponds to the system you are looking to override. For example if you wanted to override the artwork for `snes` you would create an image called `snes.webp` in the backgrounds folder.
* If a given system image is not found, then the built-in images from the theme will be used as a fallback. This allows you to customize only the images you want and still have images displayed for all systems.

### Overlays

Custom overlays can be added to help make images pop.

* If you do not have an overlay for a system, you must use a fully transparent image (you can use [this one](_inc/other/fully-transparent-overlay.webp)).
* The images must be of 1920x1080 resolution.
* Copy your custom overlay images (or the transparent ones) to the `overlays` folder previously created.
* They should be named either (in order of precedence):
    - `${system.theme}.webp`
    - `${system.theme}.png`
* As above, the `${system.theme}` variable corresponds to the system you are looking to override. This also applies to the transparent default overlay.
* If a given system image is not found, then it should fallback to the fully transparent overlay.

### Multilanguage support

The UI component "/_inc/ui-components/theme-config.xml" has now full support for Spanish, systems metadata is being updated to have Spanish support too.
Spanish works with both "es" and "es MX" setting from Batocera.

## Acknowledgments

Inspiration and templates were taken from the following themes:

- [Iconic (ES-DE)](https://github.com/Siddy212/iconic-es-de) by [Siddy212](https://github.com/Siddy212).
- [Iconic (Batocera 4:3)](https://github.com/waffledork/iconic-batocera) by [waffledork](https://github.com/waffledork).
- [Canvas (ES)](https://github.com/Siddy212/canvas-es) by [Siddy212](https://github.com/Siddy212).
- [TechDweeb (ES)](https://github.com/anthonycaccese/techdweeb-es) by [anthonycaccese](https://github.com/anthonycaccese).


This theme would not have been possible without the dedicated work of numerous artists who created the artworks, including but not limited to:

- [fagnerpc](https://github.com/fagnerpc)
- [Robert Fink](https://finklematter.artstation.com/)
- [Mark Van Haitsma](https://www.artstation.com/mvhaitsma)
- [Yoshiyaki](https://www.deviantart.com/yoshiyaki)
- [Renato Giacomo](https://www.artstation.com/renatogiacomini)
- [Vincent Moubeche](https://www.artstation.com/vincentmoubeche)
- [SonicJeremy](https://www.deviantart.com/sonicjeremy)
- [Hydro-Plumber](https://www.deviantart.com/hydro-plumber)
- [Pik](https://gamebanana.com/members/1521238)
- [Nibroc-Rock](https://www.deviantart.com/nibroc-rock)
- [Blueamnesiac](https://www.deviantart.com/blueamnesiac)
- [Adverse56](https://www.deviantart.com/adverse56)
- [Chris Silva](https://www.artstation.com/artwork/obBlyB)
- [jlcryu](https://www.deviantart.com/jlcryu)
- [EliteRobo](https://www.deviantart.com/eliterobo)
- [mikimontllo](https://twitter.com/mikimontllo)
- [Scotsman](https://forums.launchbox-app.com/profile/142250-scotsman/)
- [PangolinWrestler](https://github.com/PangolinWrestler)
- [Luis Felipe Moura](https://www.artstation.com/luizmoura)
- [ZehB](https://www.deviantart.com/zehb)
- [firei9pro](https://www.deviantart.com/firei9pro)
- [CBeanowitz](https://www.deviantart.com/cbeanowitz)
- [popmelon](https://pixabay.com/users/popmelon-15508150/)
