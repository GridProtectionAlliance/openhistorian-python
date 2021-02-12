:: Need symbolic link to README.md in docs folder so that twine can access markdown file
:: becasue files outside of current directory are sandboxed
mklink /H README.md docs\README.md