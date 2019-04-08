from pathlib import Path

with Path('misc/CNP-stopsignal-whitelist.txt').open() as f:
    subjects = [s.strip() for s in f.read().splitlines()]

cwd = Path().resolve()

fmt = '{sub}_task-stopsignal_variant-{var}_{suffix}.nii.gz'.format
for sub in subjects:
    subpath = (cwd / sub / 'func')
    subpath.mkdir(exist_ok=True, parents=True)
    for var in ['fslfeat', 'fmriprep']:
        destpath = Path() / var / ('%s_task-stopsignal' % sub) / 'stats'
        destinations = destpath.glob('*.nii.gz')
        if not destinations:
            print('%s empty or not found' % destpath)

        for dest in destpath.glob('*.nii.gz'):
            suffix = str(dest.name).split('_')[-1].split('.')[0]
            target = subpath / fmt(sub=sub, var=var, suffix=suffix)
            if not target.is_symlink():
                target.symlink_to(dest.resolve())
