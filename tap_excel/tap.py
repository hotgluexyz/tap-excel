"""Excel tap class."""

import json
import os
import pandas as pd
from typing import List
from singer_sdk import Stream, Tap
from singer_sdk import typing as th  # JSON schema typing helpers
from singer_sdk.helpers._classproperty import classproperty
from singer_sdk.helpers.capabilities import TapCapabilities
from tap_excel.client import ExcelStream

class TapExcel(Tap):
    """Excel tap class."""

    name = "tap-excel"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "files",
            th.ArrayType(
                th.ObjectType(
                    th.Property("entity", th.StringType, required=True),
                    th.Property("path", th.StringType, required=True),
                    th.Property("keys", th.ArrayType(th.StringType), required=True),
                    th.Property("sheet_name", th.StringType, required=False, default = "0")
                )
            ),
            description="An array of excel file stream settings.",
        ),
        th.Property(
            "excel_files_definition",
            th.StringType,
            description="A path to the JSON file holding an array of file settings.",
        ),
        th.Property(
            "add_metadata_columns",
            th.BooleanType,
            required=False,
            default=False,
            description=(
                "When True, add the metadata columns (`_sdc_source_file`, "
                "`_sdc_source_file_mtime`, `_sdc_source_lineno`) to output."
            ),
        ),
    ).to_dict()
    @classproperty
    def capabilities(self) -> List[TapCapabilities]:
        """Get tap capabilites."""
        return [
            TapCapabilities.CATALOG,
            TapCapabilities.DISCOVER,
        ]
    # def update_config(self):
    def get_file_configs(self) -> List[dict]:
        """Return a list of file configs.
        Either directly from the config.json or in an external file
        defined by csv_files_definition.
        """
        excel_files = self.config.get("files")
        excel_files_definition = self.config.get("excel_files_definition")
        if len(excel_files) > 1:
            self.logger.error(f"tap-excel: 'Cannot tap more than one file at a time")
            exit(1)
        if excel_files_definition:
            if os.path.isfile(excel_files_definition):
                with open(excel_files_definition, "r") as f:
                    excel_files = json.load(f)
            else:
                self.logger.error(f"tap-excel: '{excel_files_definition}' file not found")
                exit(1)
        if not excel_files:
            self.logger.error("No excel file definitions found.")
            exit(1)
        sheets = pd.ExcelFile(excel_files[0]["path"]).sheet_names
        streams = []
        for sheet in sheets:
            path_to_append = excel_files[0]["path"]
            streams.append({
                "entity": sheet,
                "path": path_to_append,
                "keys": ["Id"],
                "sheet_name": sheet
            })
        return streams
    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [
            ExcelStream(
                tap=self,
                name=file_config.get("entity"),
                file_config=file_config,
            )
            for file_config in self.get_file_configs()
        ]
if __name__ == "__main__":
    TapExcel.cli()