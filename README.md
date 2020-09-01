## Setup
- Install [Anaconda](https://www.anaconda.com/products/individual#Downloads), [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Miniforge](https://github.com/conda-forge/miniforge/releases)
- Create a new environment with the required dependencies:

   ```
   conda env create -f environment.yml
   ```
   This will create a new environment `survey-question-check`
- Activate the environment:

   ```
   conda activate survey-question-check
   ```

## Preparing for the checks
### Updating the Excel sheet
The file `data/Question Layout.xlsx` must be amended; specifically, for each
new language, two columns must be added: `title_<lang>` and `choices_<lang>`,
where `<lang>` must be replaced with a two-letter language / countrycode, e.g. `it` for Italian, `nl` for Dutch etc.

### Updating the scripts
The scripts in the `scripts` folder must be edited to include the newly added
language in the checks. Specifically, at the top of the files – right after
the `import` statements – there is a line that looks something like:
```
LANGUAGES = ('en', 'de', 'nl', 'it')
```
To add a new language, simply add the respective language code (the same you used in the Excel file). For example, to add Hungarian, you would modify this
line to read:
```
LANGUAGES = ('en', 'de', 'nl', 'it', 'hu')
```
Please note that you need to edit **both** script files, as they are
independent of each other.

## Running the checks
The scripts are located inside the `scripts` folder (you should know this by
now, because you should have edited them already. If you didn't, please read
the above instructions again, carefully.)

There are two scripts that perform the checks, `01_check_translations_reduces.py` and `02_check_translations_full.py`. The names should be quite obvious 😅
You should always start with the first script and only if no more error
messages are produced move on to the second.
