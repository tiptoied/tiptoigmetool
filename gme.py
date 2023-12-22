import sys
import os
from lib import GmeFile

def extract_gme(gme_filename):
    if not gme_filename.endswith('.gme'):
        print('Error: Invalid file format. Please provide a .gme file.')
        return

    try:
        with open(gme_filename, 'rb') as gme_file:
            gme_data = gme_file.read()
            gme = GmeFile(gme_data)

            if not os.path.exists('output'):
                os.makedirs('output')

            for i in range(len(gme.media_segments)):
                ogg_data = gme.extract_file(i)
                ogg_filename = f'output/file_{i}.ogg'

                with open(ogg_filename, 'wb') as ogg_file:
                    ogg_file.write(ogg_data)

                print(f'Extracted {ogg_filename}')

    except Exception as e:
        print(f'Error: {e}')

def build_gme(gme_filename):
    if not gme_filename.endswith('.gme'):
        print('Error: Invalid file format. Please provide a .gme file.')
        return

    try:
        gme = GmeFile(bytes())

        if not os.path.exists('output'):
            print('Error: No extracted OGG files found in the "output" folder.')
            return

        for i, ogg_filename in enumerate(sorted(os.listdir('output'))):
            ogg_path = os.path.join('output', ogg_filename)

            with open(ogg_path, 'rb') as ogg_file:
                ogg_data = ogg_file.read()

            gme.change_smart_media(ogg_data, i)

        gme.write_media_table()

        with open(gme_filename, 'wb') as new_gme_file:
            new_gme_file.write(gme.gme_file_buffer)

        print(f'Built {gme_filename} with modified OGG files.')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python gme.py [extract|build] [filename.gme]')
    else:
        command = sys.argv[1]
        filename = sys.argv[2]

        if command == 'extract':
            extract_gme(filename)
        elif command == 'build':
            build_gme(filename)
        else:
            print('Error: Invalid command. Use "extract" or "build".')
