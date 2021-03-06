import os
import subprocess
import sys

LABS = ['AFM', 'ATM', 'CO2', 'MNO', 'MOT', 'NMR', 'OPT', 'QIE', 'BMC', 'OTZ',
    'COM', 'MUO', 'GMA', 'BRA', 'RUT', 'HAL', 'LLS', 'NLD', 'JOS', 'SHE',
    'AFM_Signatures', 'ATM_Signatures', 'ATM_Signatures', 'CO2_Signatures',
    'MNO_Signatures', 'MOT_Signatures', 'NMR_Signatures', 'OPT_Signatures', 
    'QIE_Signatures', 'BMC_Signatures', 'OTZ_Signatures', 'COM_Signatures', 
    'MUO_Signatures', 'GMA_Signatures', 'BRA_Signatures', 'RUT_Signatures', 
    'HAL_Signatures', 'LLS_Signatures', 'NLD_Signatures', 'JOS_Signatures', 'SHE_Signatures']

SITE = '0bc915fe-2126-4798-9621-fdf6aa78ed57'

# Retrieve changed files in the latest git push
diff_cmd = 'git diff --name-only ' + os.environ['TRAVIS_COMMIT_RANGE']
changed_files = subprocess.check_output(
    diff_cmd.split()).decode('utf-8').split('\n')


if 'lab.cls' in changed_files:
    # If lab.cls is changed, rebuild all PDFs
    labs_to_rebuild = LABS
else:
    # Otherwise, only rebuild PDFs that have changed files
    labs_to_rebuild = set()
    for file in changed_files:
        lab = file.split('/')[0]
        if lab in LABS:
            labs_to_rebuild.add(lab)

if len(labs_to_rebuild) > 0:

    # Make a 'build' directory
    subprocess.run(['mkdir', 'build'])

    # Get the base directory for pointing to specific files
    base_dir = os.environ['TRAVIS_BUILD_DIR']

    successes, failures = [], []

    for lab in labs_to_rebuild:
        print('Rebuilding', lab)
        build_cmd = 'cd {}/{} && latexmk -outdir=../build -pdf {}'

        try:
            subprocess.run(build_cmd.format(base_dir, lab, lab),
                shell=True, timeout=60)

            # Sync the PDF to Physics lab website
            sync_cmd = ("rsync -vz --ipv4 --progress -e 'ssh -p 2222' "
                "{}/build/{}.pdf --temp-dir=~/tmp/ "
                "live.{}@appserver.live.{}.drush.in:files/writeups/")
            subprocess.run(sync_cmd.format(base_dir, lab, SITE, SITE), shell=True)

            successes.append(lab)

        except subprocess.TimeoutExpired:
            print('The timeout for {} expired.'.format(lab))
            failures.append(lab)

    if 'lab.cls' in changed_files:
        print('lab.cls file changed, so attempted to rebuild all labs.')
    else:
        print('Attempted to rebuild lab(s) with changed files:', labs_to_rebuild)

    if failures:
        if successes:
            print('Successfully rebuilt lab(s):', successes)
        print('Failed to rebuild lab(s):', failures)
        sys.exit('Not all labs were successfully rebuilt.')
    elif 'lab.cls' in changed_files:
        print('Successfully rebuilt all labs.')
    else:
        print('Successfully rebuilt all labs with changed files.')

else:
    print('No labs to rebuild.')
