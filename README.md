# gd2gs

## Description
`gd2gs` is a Python script that gets data from the source and converts them to Google
spreadsheet as it is defined in the configuration file.

## Installation

### Fedora
The script can be installed on Fedora systems by dnf from the package that is stored in this project:
```
sudo dnf install gd2gs-0.2.0-1.fc37.noarch.rpm

```

The script can be also installed from Fedora COPR using these commands:
```
sudo dnf copr enable aries/gd2gs
sudo dnf install gd2gs
```

There are required following packages to be installed:
```
python3-bugzilla
python3-google-api-client
python3-google-auth-oauthlib
python3-jira
python3-pandas
python3-pyperclip
python3-pyyaml
```

### Linux and MacOS
The script can be installed on Linux or MacOS systems by `pip`:
```
python -m pip install gd2gs-0.2.0.tar.gz
```

There are following dependencies that are installed from PyPI by the command above:
```
google-api-python-client
google-auth-oauthlib
jira
pandas
pyperclip
pyyaml
python-bugzilla
```

## Usage
```
gd2gs [-h] [-c CONFIG] [-s SHEET [SHEET ...]] [-v] [-q] [-t]
```

The script updates data rows in the Google spreadsheet according to key values. If a key value is missing or placed inappropriately, it should be manually corrected. Then the script can update the related data. Missing key values are stored in clipboard separated with new lines which enables them to be easily copied into the spreadsheet.

`-c CONFIG` defines the name of YAML configuration file containing the input identification with access attributes, the reference to the target Google spreadsheet with names of sheets and related queries, the column names with the related items and additional parameters that define the content of the spreadsheet. If `-c` parameter is not set then `gd2gs.yaml` file from the working directory is used.

`-s SHEET` determines which sheets are processed. The selected sheets can be any sheets that are set up in the configuration YAML file. If the parameter does not occur, then all sheets, which are listed in the configuration file, are handled.

The script reports warnings and errors by default. `-v` parameter extends the level of logging with info level and `-vv` with debug level. `-q` parameter reduces the logging to errors only.

Parameter `-t` disables Google spreadsheet update.

`-h` parameter shows a short help message.

## Configuration file structure
The configuration file contains reserved words written in capital letters and additional data defining a transition of input data to the target Google spreadsheet.

Bugzilla REST API documentation: [https://wiki.mozilla.org/Bugzilla:REST_API](https://wiki.mozilla.org/Bugzilla:REST_API)

Jira REST API documentation: [https://developer.atlassian.com/server/jira/platform/rest-apis/](https://developer.atlassian.com/server/jira/platform/rest-apis/)

Jira structured data including custom field IDs and names can be found in XML data exported from Jira.

| Reserved word    | Description |
| ---------------- | ----------- |
| `API_KEY`        | File name that contains API key to access Bugzilla. |
| `BUGZILLA`       | The script takes data from Bugzilla. It should contain `API_KEY`, `DOMAIN` and `URL`, optionally `MAX_RESULTS`. |
| `CONDITION`      | It is used together with `FROM` and `GET` reserved words to define a condition which should be fulfilled to obtain required data from the input. |
| `DELIMITER`      | Delimiter is used for separation items in one cell. The default value is space. Delimiter can be defined globally as well as individually in sheets and columns. If `DELIMITER` is defined together with `GET` reserved word, then it defines a separator between items obtained from the `GET` list. |
| `DOMAIN`         | Bugzilla domain. |
| `FROM`           | It is used together with `GET` (and optionally with `CONDITION`) reserved word to address the higher level of structured identifiers. |
| `GET`            | It is used together with `FROM` (and optionally with `CONDITION`) reserved word to address the list of lower level structured identifiers with explicit value which can be regular expressions. |
| `HEADER_OFFSET`  | The first row of Google spreadsheet is expected to be the header. In this case, `HEADER_OFFSET` is 0 which is the default value. If the header is larger, `HEADER_OFFSET` defines the value. If can be either global or specific in each sheet. |
| `JIRA`           | The script takes data from Jira. It should contain `SERVER` and `TOKEN`, optionally `MAX_RESULTS`. |
| `KEY`            | The column containing keys is identified by `KEY` reserved word with `True` value. It can be either global or specific in each sheet. |
| `LINK`           | It can be used in columns. It contains URL that is used as a prefix of values. If the column is key column, link format is used. |
| `MAX_RESULTS`    | It defines maximum number of obtained items from Jira for each query. It can be only a part of `JIRA` section. |
| `NAME`           | It defines name of each sheet. |
| `QUERY`          | Query definition in each sheet. It is specific per input. |
| `SERVER`         | URL of Jira server. It can be only a part of `JIRA` section. |
| `SHEET_COLUMNS`  | Definition of columns names and their relation to data identifiers obtained from the input. It can be either global or specific in each sheet. |
| `SHEETS`         | List of sheets that should be addressed in the target Google spreadsheet. |
| `SOURCE`         | It defines columns name relation to a data identifier obtained from the input. It is used when more reserved words are belonging to the specific column, like `CONDITION`, `FROM`, `GET`, `KEY`, `LINK`. |
| `SPREADSHEET_ID` | ID of the target Google spreadsheet. |
| `TOKEN`          | File name that contains token to access Jira. |
| `URL`            | Bugzilla URL. |

### Bugzilla example
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

## Authorized access
### Bugzilla
Bugzilla access is handled using API key as described at [https://bugzilla.readthedocs.io/en/latest/api/core/v1/general.html#authentication](https://bugzilla.readthedocs.io/en/latest/api/core/v1/general.html#authentication). API key can be generated in Preferences of the personal Bugzilla profile and stored in a file that is referred in the YAML configuration file of the script.

### Jira
The script uses REST API that requires an API token. The token can be generated from your Jira account according to the guidance here: [https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html). The stored token file must be referred in the YAML configuration file of the script.

### Google
As there is used the Google spreadsheet to write data, the script requests an authorized access using JSON key file which can be obtained according to instructions here: [https://developers.google.com/workspace/guides/create-credentials#service-account](https://developers.google.com/workspace/guides/create-credentials#service-account). An easy way to provide service account credentials is by setting the GOOGLE_APPLICATION_CREDENTIALS environment variable; the script will use the value of this variable to find the service account key JSON file.

## Support
Issues can be raised by the standard way in this GitHub project.
