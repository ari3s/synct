Name:		synct
Version:	1.5.3
Release:	%autorelease
Summary:	Get data to Google or Excel sheets

License:	GPL-3.0-or-later
URL:		https://github.com/ari3s/synct
Source0:	https://raw.githubusercontent.com/ari3s/synct/main/%{name}-%{version}.tar.gz
BuildArch:	noarch

BuildRequires:	pyproject-rpm-macros
BuildRequires:	python3-devel

%description
synct reads data from the particular source and copies the data in Google
or Excel spreadsheet as it is defined in the config file. The config file
also contains relations between the source items and the columns
in the target spreadsheet.

%prep
%autosetup -p1

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files %{name}

%check
%pyproject_check_import

%files -f %{pyproject_files}
%doc README.md
%license COPYING
%{_bindir}/%{name}

%changelog
%autochangelog
