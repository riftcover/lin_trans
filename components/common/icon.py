from enum import Enum


class LinIcon(Enum):
    EXPORT = "MaterialSymbolsExportNotes"

    def path(self):
        return f':/icon/assets/icons/{self.value}.svg'
