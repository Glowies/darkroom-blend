# TODO
- [ ] Mark Compositor node groups as 'Fake User' so that they get saved properly
- [ ] Embed ICCProfiles in output image
- [ ] Find a cleaner way of getting all available colorspaces and making a dropdown/enum out of them.
- [ ] Add a few 'default' settings to use when we first make a compositor graph for a picture:
  - Exposure
  - Input Color Space
  - Grading Color Space
- [ ] Add a way to mark images for 'export' and a 'mass export' button

# Metadata situation
Dealing with Metadata is a little annoying, partly because of Blender and partly because of OpenImageIO
- For JPEGs, Blender does NOT write ICC Profile attributes to a jpg render; however, it does embed them in the JPG header! Plus, using OpenImageIO, at least we can write EXIF attributes into the JPEGs. UNFORTUNATELY, when we rewrite the JPEG using OpenImageIO, for some reason, it falls back to the sRGB Color Profile again... even if Blender exported and wrote a DisplayP3. Also, for some reason, OpenImageIO insists on recompressing the jpg, even if we specify lossless compression in the metadata....
- For WebP, Blender does write ICC Profile into them; however, OpenImageIO does not support writing EXIF metadata into WebP outputs :(
- TIFF is one format where both requirements are held. However, TIFF is a propriatary format owned by Adobe now :/
- PNG is also another where both are held. However, OIIO takes forever to re-export the PNG with the same metadata.. I should try ONLY changing the metadata

## Solution
The least dirty solution to me was this:
1. Make a JPEG copy of the original raw image using OpenImageIO. This will contain the EXIF metadata that we want.
2. Render either a WEBP or JPEG from Blender. These will contain the valid color profile metadata in them.
3. Use piexif to transfer EXIF data from the JPEG copy to the render.
