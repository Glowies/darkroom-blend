import os
import subprocess
import argparse

def convert_raw_to_exr(input_dir, output_dir, colorspace, compression):
    """
    Converts all .ARW or .arw images in a directory to .exr format
    using oiiotool.
    """
    # Check if the input directory exists
    if not os.path.isdir(input_dir):
        print(f"Error: The input directory '{input_dir}' does not exist.")
        sys.exit(1) # Exit with a non-zero status code to indicate an error

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Loop through all files in the input directory
    for filename in os.listdir(input_dir):
        # Ignore dotfiles
        if filename.startswith('.'):
            continue

        input_path = os.path.join(input_dir, filename)
        
        # Construct the output filename by changing the extension to .exr
        output_filename = os.path.splitext(filename)[0] + '.exr'
        output_path = os.path.join(output_dir, output_filename)
        
        # Construct the oiiotool command
        command = [
            'oiiotool',
            '-i', input_path,
            '-tocolorspace', colorspace,
            '--compression', compression,
            '-o', output_path
        ]
        
        print(f"Converting {input_path} to {output_path}...")
        
        try:
            # Execute the command
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error converting {input_path}: {e}")

if __name__ == "__main__":
    # Define your input and output directories
    parser = argparse.ArgumentParser(description='Convert ARW images to EXR format.')
    
    # Define command-line arguments
    parser.add_argument(
        '--input', 
        '-i', 
        type=str, 
        default='.', 
        help='The input directory containing the raw images. (default: ".")'
    )
    parser.add_argument(
        '--output', 
        '-o', 
        type=str, 
        default='exr', 
        help='The output directory to save the EXR images. (default: "exr")'
    )

    parser.add_argument(
        '--colorspace', 
        '-c', 
        type=str, 
        default='aces_interchange', 
        help='The color space to output the EXR images in. (Needs to be a valid color space name or alias given in your OCIO config)'
    )

    parser.add_argument(
        '--compression', 
        '-x', 
        type=str, 
        default='piz', 
        help='The EXR compression method to be used. Lossless compression options are: ZIP, ZIPS, PIZ, RLE'
    )
    
    # Parse the arguments from the command line
    args = parser.parse_args()
    
    # Call the conversion function with the parsed arguments
    convert_raw_to_exr(args.input, args.output, args.colorspace, args.compression)

    print("\nConversion complete!")
