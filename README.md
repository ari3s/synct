# synct

## Description

`synct` (derived from *synchronize tables*) is a Python script that retrieves data from a source and converts it to either a Google or Excel spreadsheet as defined in the configuration file.

## Installation

### Fedora

The script can be installed on Fedora systems using `dnf` with the package stored in this project:

```
sudo dnf install synct-1.7.0-1.fc40.noarch.rpm
```

Alternatively, you can install the script from Fedora COPR using these commands:

```
sudo dnf copr enable aries/synct
sudo dnf install synct
```

The following packages are required:

```
python3-bugzilla
python3-google-api-client
python3-google-auth-oauthlib
python3-jira
python3-openpyxl
python3-pandas
python3-pyperclip
python3-pyyaml
```

### Linux and MacOS

The script can be installed on Linux or MacOS systems using `pip`:

```
python -m pip install synct-1.7.0.tar.gz
```

The following dependencies will be installed from PyPI by the above command:

```
google-api-python-client
google-auth-oauthlib
jira
openpyxl
pandas
pyperclip
pyyaml
python-bugzilla
```

## Usage

```
synct [-h] [--version] \
      [-c CONFIG] [-s SHEET [SHEET ...]] \
      [-a] [-r] [-n] \
      [-f FILE] [-t TABLE] [-o OFFSET] \
      [-v] [-q]
```

The script updates data rows in the target Google or Excel spreadsheet based on key values. If a key value is missing or placed inappropriately, it should be manually corrected. The script can then update the related data. Missing key values are stored in the clipboard, separated by new lines, which allows for easy copying into the spreadsheet.

### Options

- `-h`, `--help`
  - Show help message with a list of options and their descriptions, and exit without any action.

- `--version`
  - Display the script name and version, then exit without any action.

- `-c CONFIG`, `--config CONFIG`
  - Specify the name of the YAML configuration file containing the input identification with access attributes, a reference to the target spreadsheet with sheet names and related queries, column names with their related items, and additional parameters defining the content of the spreadsheet. If this option is not specified, the script uses the `synct.yaml` file in the working directory.

- `-s SHEET [SHEET ...]`, `--sheet SHEET [SHEET ...]`
  - Specify which sheets to processed. The selected sheets can be any sheets defined in the configuration YAML file. If this option is not specified, all sheets listed in the configuration file will be processed.

- `-a`, `--add`
  - Enable the addition of missing rows to the spreadsheet. The added rows are placed at the end of the specific sheet.

- `-n`,` --noupdate`
  - Disable updating the target spreadsheet.

- `-r`, `--remove`
  - Enable the removal of rows in the spreadsheet. This option is relevant for rows whose values are not retrieved from the source. For example, if the script is configured to collect and update open bugs from Bugzilla, the `-r` parameter allows the deletion of rows containing bugs that aro no longer retrieved, such as those that have been closed. Without this option, such rows are not updated, and a warning is reported by the script.

- `-f FILE`, `--file FILE`
  - Specify the source file name, which can be an Excel or OpenDocument spreadsheet or a CSV file. If this parameter is used, the source file defined in the configuration file is ignored.

- `-t TABLE`, `--table TABLE`
  - Specify the table/sheet in the source file to be used. If this parameter is used, the table name defined in the configuration file is ignored.

- `-o OFFSET`, `--offset OFFSET`
  - Define the header offset in the source file. If this parameter is used, the offset defined in the configuration file is ignored. The default value is 0.

- `-v `, `--verbose`
  - By default, the script reports warnings and errors. The `-v` parameter increases the logging level to include the informational messages. Repeating the option (`-vv`) increases verbosity further to include the debug messages.

- `-q` , `--quiet`
  - Reduce logging to errors only.

## Configuration file structure

The configuration file contains reserved words written in capital letters, as well as additional data that defines the transition of input data to the target spreadsheet.

Bugzilla REST API documentation: [https://wiki.mozilla.org/Bugzilla:REST_API](https://wiki.mozilla.org/Bugzilla:REST_API)

GitHub REST API documentation: [https://docs.github.com/en/rest](https://docs.github.com/en/rest)

GitLab REST API documentation: [https://docs.gitlab.com/ee/api/rest/](https://docs.gitlab.com/ee/api/rest/)

Jira REST API documentation: [https://developer.atlassian.com/server/jira/platform/rest-apis/](https://developer.atlassian.com/server/jira/platform/rest-apis/)

Jira structured data, including custom field IDs and names, can be found in XML data exported from Jira.

| Reserved word      | Description |
| ------------------ | ----------- |
| `API_KEY`          | File name containing API key to access Bugzilla. |
| `BUGZILLA`         | Specifies that the script retrieves data from Bugzilla. It should contain `API_KEY`, `DOMAIN`, and `URL`. |
| `CONDITION`        | Used with the `FROM` and `GET` reserved words to define a condition that must be met to obtain the required data from the input. |
| `DEFAULT_COLUMNS`  | Enables the use of default column names. This means they can be omitted in the configuration file, and source data items and target spreadsheet columns with matching names are paired automatically. The reserved word value can be either 'True' or 'False' and can be defined either globally or specifically for each sheet. This option is globally set to 'False' by default. |
| `DELIMITER`        | The delimiter separates items in one cell. The default value is a space. The delimiter can be defined globally or individually for sheets and columns. If `DELIMITER` is defined together with the `GET` reserved word, it defines a separator between items obtained from the `GET` list. |
| `DOMAIN`           | Bugzilla domain. |
| `FILE`             | Specifies that the script retrieves data from a local file in spreadsheet format (.ods, .xls, .xlsx, .csv). It should contain `TYPE`, optionally `FILE_NAME`, `OFFSET` and/or `TABLE`. |
| `FILE_NAME`        | Name of the input file (optional). It is ignored if a file name is defined on the command line. |
| `FROM`             | Used with the `GET` (and optionally with the `CONDITION`) reserved word to address the higher level of structured identifiers. |
| `GET`              | Used with the `FROM` (and optionally with the `CONDITION`) reserved word to address the list of lower-level structured identifiers with explicit values, which can be regular expressions. |
| `GITHUB`           | Specifies that the script retrieves data from GitHub. It should contain `SEARCH_API` and `TOKEN`. |
| `GITLAB`           | Specifies that the script retrieves data from GitLab. It should contain `SEARCH_API` and `TOKEN`. |
| `HEADER_OFFSET`    | The first row of the target spreadsheet is expected to be the header. In this case, `HEADER_OFFSET` is 0, which is the default value. If the header spans multiple rows, `HEADER_OFFSET` defines the value. It can be defined either globally or specifically for each sheet. |
| `INHERIT_FORMULAS` | Enables formula inheritance in added rows from the last original row in the columns that are not included in the source data. The reserved word value can be either 'True' or 'False' and can be defined either globally or specifically for each sheet or column. This option is globally set to 'False' by default. |
| `JIRA`             | Specifies that the script retrieves data from Jira. It should contain `SERVER` and `TOKEN`, optionally `MAX_RESULTS`. |
| `KEY`              | The column containing keys is identified by the `KEY` reserved word with a value of `True`. It can be defined either globally or specifically for each sheet. |
| `LINK`             | Used in columns, it contains a URL that is used as a prefix for values. If the column is a key column, link format is used. |
| `MAX_RESULTS`      | Defines the maximum number of items obtained from Jira for each query (pagination is supported). The default value is 100. It can only be part of the `JIRA` section. |
| `NAME`             | Defines the name of each sheet. |
| `OFFSET`           | Header offset in the spreadsheet input file (optional). It is ignored if an offset is defined on the command line. |
| `OPTIONAL`         | When the key with this specific column value is missing, it is not reported as a warning. The value can be a regular expression. |
| `QUERY`            | Query definition for each sheet. It is specific to the input: Bugzilla queries are in YAML format, GitHub queries follow the GitHub Search API rules, and GitLab queries follow GitLab Search API rules. Jira queries are written JIRA Query Language (JQL), and queries for spreadsheets are in Pandas query format. |
| `SEARCH_API`       | URL of the GitHub or GitLab search API. It can only be a part of the `GITHUB` or `GITLAB` section. |
| `SERVER`           | URL of the Jira server. It can only be a part of the `JIRA` section. |
| `SHEET_COLUMNS`    | Reserved word defining of column names and their relation to data identifiers obtained from the input. It can be defined either globally or specifically for each sheet. |
| `SHEETS`           | List of sheets in the target spreadsheet. |
| `SOURCE`           | Reserved word defining the column name's relation to the data identifier obtained from the input. It is used when multiple reserved words belong to a specific column, such as `CONDITION`, `FROM`, `GET`, `KEY`, `LINK`, or `OPTIONAL`. |
| `SPREADSHEET`      | Name of the target Excel spreadsheet. |
| `SPREADSHEET_ID`   | ID of the target Google spreadsheet. |
| `TABLE`            | Table/sheet name of the spreadsheet source (optional). Only one table is allowed. It is ignored if a table name is defined on the command line. |
| `TOKEN`            | The file name containing the token to access GitHub, GitLab or Jira. |
| `TYPE`             | Type of the local input file. It must contain the value `SPREADSHEET`. |
| `URL`              | Bugzilla URL. |

### Configuration file examples

Configuration file examples for different data source types can be found in [the examples directory](https://github.com/ari3s/synct/tree/main/examples).

## Authorized access

### Bugzilla

Bugzilla access is handled using an API key, as described at [https://bugzilla.readthedocs.io/en/latest/api/core/v1/general.html#authentication](https://bugzilla.readthedocs.io/en/latest/api/core/v1/general.html#authentication). An API key can be generated in the Preferences of the personal Bugzilla profile and stored in a file referred to in the YAML configuration file of the script.

### GitHub

The script uses the REST API, which can use an API token generated according to the guidance here: [https://docs.github.com/en/rest/overview/authenticating-to-the-rest-api](https://docs.github.com/en/rest/overview/authenticating-to-the-rest-api). The stored token file must be referred to in the YAML configuration file of the script.

### GitLab

The script uses the REST API, which uses an API token generated according to the guidance here: [https://docs.gitlab.com/ee/api/rest/#authentication](https://docs.gitlab.com/ee/api/rest/#authentication). The stored token file must be referred to in the YAML configuration file of the script.

### Jira

The script uses the REST API, which requires an API token. The token can be generated from your Jira account according to the guidance here: [https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html). The stored token file must be referred to in the YAML configuration file of the script.

### Google

To use the Google Sheets API to read and write data, the script requires authorized access using OAuth 2.0 credentials in the form of a service account JSON key file. Follow these steps to set up the necessary credentials:

1. **Create Service Account Credentials**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Select your project or create a new one.
   - Navigate to **APIs & Services** > **Credentials**.
   - Click on **Create credentials** and select **Service account**.
   - Follow the prompts to set up a service account. You may choose a descriptive name, role, and other settings.

2. **Download the JSON Key File**
   - Once the service account is created, go to the **Keys** section.
   - Click **Add Key** > **Create new key**.
   - Choose **JSON** and download the key file. Save it in a secure location, for example in `.google/google_credentials.json` file in you home directory.

3. **Enable Required APIs**
   - Navigate to **APIs & Services** > **Library**.
   - Enable the following APIs for your project:
     - **Google Sheets API**
     - **Google Drive API**

4. **Set Up Environment Variable for Credentials**
   - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your downloaded JSON key file. This variable allows your script to authenticate using the service account credentials.

5. **Configure OAuth Consent Screen**
   - Navigate to **APIs & Services** > **OAuth consent screen**.
   - Choose **Internal** or **External** based on your usage.
   - Complete the required fields. If you use sensitive or restricted scopes, you'll need to go through the verification process.

6. **Set OAuth Scopes**
   Make sure that your OAuth consent screen allows access to the necessary Google Sheets API scopes:

   | API               | Scope                         | User-facing description                                |
   | ----------------- | ----------------------------- | ------------------------------------------------------ |
   | Google Sheets API | `https://www.googleapis.com/auth/spreadsheets` | See, edit, create, and delete all your Google Sheets spreadsheets |

## Support

Bugs can be reported or new feature requests can be raised in the [Issues](https://github.com/ari3s/synct/issues) section.
