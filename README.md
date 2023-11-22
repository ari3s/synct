# synct

## Description
`synct` (derived from *synchronize tables*) is a Python script that retrieves data from a source and converts it to either Google or Excel spreadsheet as defined in the configuration file.

## Installation

### Fedora
The script can be installed on Fedora systems using `dnf` from the package stored in this project:
```
sudo dnf install synct-1.3.0-1.fc39.noarch.rpm

```

The script can also be installed from Fedora COPR using these commands:
```
sudo dnf copr enable aries/synct
sudo dnf install synct
```

The following packages are required to be installed:
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
python -m pip install synct-1.3.0.tar.gz
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
synct [-h] [-c CONFIG] [-s SHEET [SHEET ...]] [-a] [-r] [-f FILE] [-t TABLE] [-o OFFSET] [-v] [-q] [-n]
```

The script updates data rows in the target Google or Excel spreadsheet based on key values. If a key value is missing or placed inappropriately, it should be manually corrected. Then the script can update the related data. Missing key values are stored in the clipboard, separated by new lines, which allows for easy copying into the spreadsheet.

The `-c CONFIG` parameter defines the name of the YAML configuration file containing the input identification with access attributes, a reference to the target spreadsheet with sheet names and related queries, column names with their related items, and additional parameters defining the content of the spreadsheet. If the `-c` parameter is not set, the script uses the `synct.yaml` file in the working directory.

The `-s SHEET` parameter determines which sheets are processed. The selected sheets can be any sheets defined in the configuration YAML file. If the parameter is not specified, all sheets listed in the configuration file will be processed.

The `-a` parameter enables the addition of missing rows to the spreadsheet. The added rows are placed at the end of the specific sheet.

The `-r` parameter enables the removal of rows in the spreadsheet. It is related to rows whose values are not retrieved from a source. For example, the script is configured to collect and update open bugs from Bugzilla. The `-r` parameter allows for the deletion of rows containing bugs that have not been retrieved, meaning those that have been closed. Without the parameter, such rows are not updated, and a warning is reported by the script.

The `-f FILE` parameter defines the source file name that can be either Excel or OpenDocument spreadsheet or CSV file. If the parameter occurs, the source file in the configuration file is ignored.

The `-t TABLE` parameter defines the table/sheet in the source file that will be used. If the parameter occurs, a table name in the configuration file is ignored.

The `-o OFFSET` parameter defines the header offset in the source file. If the parameter occurs, an offset in the configuration file is ignored. Default value is 0.

By default, the script reports warnings and errors. The `-v` parameter extends the logging level to include the info level, and `-vv` includes the debug level. The `-q` parameter reduces the logging to errors only.

The `-n` parameter disables updating the target spreadsheet.

The `-h` parameter displays a short help message.

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
| `BUGZILLA`         | The script retrieves data from Bugzilla. It should contain `API_KEY`, `DOMAIN`, and `URL`, optionally `MAX_RESULTS`. |
| `CONDITION`        | Used with the `FROM` and `GET` reserved words to define a condition that must be met to obtain the required data from the input. |
| `DEFAULT_COLUMNS`  | Enables usage of default column names. It means they can be omitted in the configuration file, and equal names of source data items and target spreadsheet columns are paired. The reserved word value can be either 'True' or 'False' and can be defined either globally or specifically for each sheet. This option is globally set to 'False' by default. |
| `DELIMITER`        | The delimiter separates items in one cell. The default value is space. The delimiter can be defined globally as well as individually in sheets and columns. If `DELIMITER` is defined together with the `GET` reserved word, it defines a separator between items obtained from the `GET` list. |
| `DOMAIN`           | Bugzilla domain. |
| `FILE`             | The script retrieves data from local file in spreadsheet format (.ods, .xls, .xlsx, .csv). It should contain `TYPE`, optionally 'FILE_NAME', `OFFSET' and/or `TABLE`. |
| `FILE_NAME`        | Name of the input file (optional). It is ignored if a file name is defined on the command line. |
| `FROM`             | Used with the `GET` (and optionally with the `CONDITION`) reserved word to address the higher level of structured identifiers. |
| `GET`              | Used with the `FROM` (and optionally with the `CONDITION`) reserved word to address the list of lower level structured identifiers with explicit values, which can be regular expressions. |
| `GITHUB`           | The script retrieves data from GitHub. It should contain `SEARCH_API` and `TOKEN`. |
| `GITLAB`           | The script retrieves data from GitLab. It should contain `SEARCH_API` and `TOKEN`. |
| `HEADER_OFFSET`    | The first row of the target spreadsheet is expected to be the header. In this case, `HEADER_OFFSET` is 0, which is the default value. If the header is larger, `HEADER_OFFSET` defines the value. It can be defined either globally or specifically for each sheet. |
| `INHERIT_FORMULAS` | Enables formula inheritance in added rows from the last original row in the columns that are not included in the source data. The reserved word value can be either 'True' or 'False' and can be defined either globally or specifically for each sheet or column. This option is globally set to 'False' by default. |
| `JIRA`             | The script retrieves data from Jira. It should contain `SERVER` and `TOKEN`, optionally `MAX_RESULTS`. |
| `KEY`              | The column containing keys is identified by the `KEY` reserved word with a value of `True`. It can be defined either globally or specifically for each sheet. |
| `LINK`             | Used in columns, it contains a URL that is used as a prefix for values. If the column is a key column, link format is used. |
| `MAX_RESULTS`      | Defines the maximum number of obtained items from Jira for each query. It can only be a part of the `JIRA` section. |
| `NAME`             | Defines the name of each sheet. |
| `OFFSET`           | Header offset in the spreadsheet input file (optional). It is ignored if an offset is defined on the command line. |
| `OPTIONAL`         | When the key with this specific column value is missing, it is not reported as a warning. The value can be a regular expression. |
| `QUERY`            | Query definition for each sheet. It is specific to the input: Bugzilla queries are in YAML format, GitHub and GitLab queries contain searching parameters of search API URL, Jira queries are in JIRA Query Language (JQL), and queries for spreadsheets are in Pandas query format. |
| `SEARCH_API`       | URL of the GitHub or GitLab search API. It can only be a part of either `GITHUB` or `GITLAB` section. |
| `SERVER`           | URL of the Jira server. It can only be a part of the `JIRA` section. |
| `SHEET_COLUMNS`    | Definition of column names and their relation to data identifiers obtained from the input. It can be defined either globally or specifically for each sheet. |
| `SHEETS`           | List of sheets that should be addressed in the target spreadsheet. |
| `SOURCE`           | Defines the column name's relation to a data identifier obtained from the input. It is used when multiple reserved words belong to a specific column, such as `CONDITION`, `FROM`, `GET`, `KEY`, `LINK`, or `OPTIONAL`. |
| `SPREADSHEET`      | Name of the target Excel spreadsheet. |
| `SPREADSHEET_ID`   | ID of the target Google spreadsheet. |
| `TABLE`            | Table/sheet name of the spreadsheet source (optional). Only one table is allowed. It is ignored if a table name is defined on the command line. |
| `TOKEN`            | File name that contains the token to access GitHub, GitLab or Jira. |
| `TYPE`             | Type of the local input file. The value must be `SPREADSHEET`. |
| `URL`              | Bugzilla URL. |

### Bugzilla YAML configuration file example
```
BUGZILLA:
  DOMAIN: bugzilla.redhat.com
  URL: https://bugzilla.redhat.com/xmlrpc.cgi
  API_KEY: ~/.config/python-bugzilla/bugzillarc
SPREADSHEET_ID: 1ftibl011mzlge8gcJ0MfmvIw_C8Hq2iYeUdU6B-rbwI
DELIMITER: ", "
HEADER_OFFSET: 0
SHEET_COLUMNS:
  Bug ID:
    SOURCE: id
    KEY: True
    LINK: https://bugzilla.redhat.com/show_bug.cgi?id=
  Component: component
  Status: status
  Summary: summary
  Assignee: assigned_to
  Priority: priority
  Flags:
    DELIMITER: " "
    SOURCE:
      DELIMITER: ""
      FROM: flags
      GET:
      - name: .*
        status: .*
  Opened: creation_time
SHEETS:
  - NAME: rpm
    QUERY:
        query_format: advanced
        include_fields:
        - _default
        - flags
        - external_bugs
        product: Fedora
        component: rpm
        status: __open__
        limit: 100
  - NAME: libdnf
    QUERY:
        query_format: advanced
        include_fields:
        - _default
        - flags
        - external_bugs
        product: Fedora
        component: libdnf
        status: __open__
        limit: 100
    SHEET_COLUMNS:
      Jira:
        SOURCE:
          FROM: external_bugs
          GET:
          - ext_bz_bug_id: .*
          CONDITION:
            type:
              type: JIRA
          LINK: https://issues.redhat.com/browse/
```

### GitHub YAML configuration file example
```
GITHUB:
  SEARCH_API: "https://api.github.com/search/"
  TOKEN: "~/.github/github_token"
SPREADSHEET_ID: 1aEHCYma8orzDiDbkOnDifoFL2LuOy4b0aVAD1j7NTPg
HEADER_OFFSET: 2
SHEET_COLUMNS:
  Issue Number: 
    SOURCE: number
    KEY: true
    LINK: https://github.com/ari3s/synct/issues/
  Title: title
  Assignee:
    SOURCE:
      FROM: assignees
      GET:
        - login: .*
  Label:
    SOURCE:
      FROM: labels
      GET:
        - name: .*
  Status: state
  Created: created_at
  Updated: updated_at
  Closed: closed_at
SHEETS:
- NAME: Issues
  QUERY: issues?q=state:open+state:closed+repo:ari3s/synct
```

### GitLab YAML configuration file example
```
GITLAB:
  SEARCH_API: "https://gitlab.cee.redhat.com/api/v4/groups/"
  TOKEN: "~/.gitlab/gitlab_token"
SPREADSHEET_ID: 1jj2EI5Kum7Q2_DgJMKGAAP7bzCwOOX_WBOZ9AussSZo
HEADER_OFFSET: 2
SHEET_COLUMNS:
  Issue Number:
    SOURCE: iid
    KEY: true
    LINK: https://gitlab.cee.redhat.com/developer-guide/developer-guide/-/issues/
  Title: title
  Assignee:
    SOURCE:
      FROM: assignees
      GET:
        - name: .*
  Label: labels
  Status: state
  Created: created_at
  Updated: updated_at
  Closed: closed_at
SHEETS:
- NAME: Issues
  DELIMITER: "\n"
  QUERY: 9649/search?scope=issues&search=file
```

### Jira YAML configuration file example
```
JIRA:
  SERVER: https://issues.redhat.com/
  TOKEN: "~/.jira/jira.token"
  MAX_RESULTS: '1000'
SPREADSHEET_ID: 1RuA01d-Asa6EKhZ9HJU7ykXk-wHjX3SIUsEgScS3ONM
SHEETS:
- NAME: rpm
  QUERY: project = RHEL AND component = rpm AND issuetype = Bug
SHEET_COLUMNS:
  Issue key:
    SOURCE: key
    KEY: True
    LINK: https://issues.redhat.com/browse/
  Title: fields.summary
  Assignee: fields.assignee
  Priority: fields.priority
  Fix Versions: fields.fixVersions
  Affects Versions: fields.versions
  Label: fields.labels
  Issue status: fields.status
```

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
Since the script uses the Google Sheets API to read and write data, it requires authorized access using an OAuth JSON key file, which can be obtained according to the instructions here: [https://developers.google.com/workspace/guides/create-credentials#service-account](https://developers.google.com/workspace/guides/create-credentials#service-account).

The following *Enabled APIs & Services* should be selected: *Cloud Identity-Aware Proxy API*, *Google Sheets API*, and *Token Service API*. Sensitive scopes set through the *OAuth consent screen* should allow the following option:

| API               | Scope                 | User-facing description |
| ----------------- | --------------------- | ----------------------- |
| Google Sheets API | .../auth/spreadsheets | See, edit, create, and delete all your Google Sheets spreadsheets |

The OAuth client ID type set in the *Credentials* menu should be *Desktop*. The OAuth client JSON file with service account credentials should be downloaded and stored locally. An easy way to provide service account credentials is by setting the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the JSON file's name. The script will use the value of this variable to find the service account key JSON file.

## Support
Issues can be raised using the standard method in this GitHub project.
