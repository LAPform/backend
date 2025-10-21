"""
Utilitaires d'export pour FormForge
"""

import csv
import io
import json
from typing import List, Dict, Any
from datetime import datetime
# import pandas as pd  # Supprimé pour éviter les problèmes de compilation


class CSVExporter:
    """Exportateur CSV pour les réponses"""

    @staticmethod
    def generate_csv(data: List[Dict], encoding: str = "utf-8") -> str:
        """Générer un CSV à partir des données"""
        if not data:
            return ""

        output = io.StringIO()

        # Obtenir toutes les clés uniques
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())

        # Trier les clés pour un ordre cohérent
        fieldnames = sorted(all_keys)

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in data:
            # Nettoyer les valeurs pour CSV
            cleaned_row = {}
            for key, value in row.items():
                if isinstance(value, (dict, list)):
                    cleaned_row[key] = json.dumps(value, ensure_ascii=False)
                elif value is None:
                    cleaned_row[key] = ""
                else:
                    cleaned_row[key] = str(value)

            writer.writerow(cleaned_row)

        return output.getvalue()

    @staticmethod
    def save_csv_file(data: List[Dict], filename: str) -> str:
        """Sauvegarder un CSV dans un fichier"""
        csv_content = CSVExporter.generate_csv(data)

        with open(filename, "w", encoding="utf-8", newline="") as f:
            f.write(csv_content)

        return filename


class ExcelExporter:
    """Exportateur Excel pour les réponses (version simplifiée)"""

    @staticmethod
    def generate_excel(data: List[Dict]) -> bytes:
        """Générer un fichier Excel à partir des données (version CSV)"""
        if not data:
            return b""

        # Générer un CSV au lieu d'Excel pour éviter pandas
        csv_content = CSVExporter.generate_csv(data)
        return csv_content.encode('utf-8')

    @staticmethod
    def save_excel_file(data: List[Dict], filename: str) -> str:
        """Sauvegarder un fichier Excel (version CSV)"""
        # Sauvegarder comme CSV au lieu d'Excel
        csv_filename = filename.replace('.xlsx', '.csv')
        CSVExporter.save_csv_file(data, csv_filename)
        return csv_filename


class JSONExporter:
    """Exportateur JSON pour les réponses"""

    @staticmethod
    def generate_json(data: List[Dict], pretty: bool = True) -> str:
        """Générer un JSON à partir des données"""
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        else:
            return json.dumps(data, ensure_ascii=False, default=str)

    @staticmethod
    def save_json_file(data: List[Dict], filename: str, pretty: bool = True) -> str:
        """Sauvegarder un fichier JSON"""
        json_content = JSONExporter.generate_json(data, pretty)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(json_content)

        return filename


class ExportManager:
    """Gestionnaire d'export unifié"""

    @staticmethod
    def export_responses(
        data: List[Dict], format: str = "csv", filename: str = None
    ) -> Dict[str, Any]:
        """Exporter les réponses dans le format demandé"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not filename:
            filename = f"form_responses_{timestamp}"

        result = {
            "success": True,
            "format": format,
            "filename": filename,
            "timestamp": timestamp,
            "total_records": len(data),
        }

        try:
            if format.lower() == "csv":
                content = CSVExporter.generate_csv(data)
                result["content"] = content
                result["mime_type"] = "text/csv"
                result["extension"] = ".csv"

                elif format.lower() == "excel":
                    content = ExcelExporter.generate_excel(data)
                    result["content"] = content
                    result["mime_type"] = "text/csv"  # CSV au lieu d'Excel
                    result["extension"] = ".csv"  # CSV au lieu d'Excel

                elif format.lower() == "json":
                    content = JSONExporter.generate_json(data)
                    result["content"] = content
                    result["mime_type"] = "application/json"
                    result["extension"] = ".json"

            else:
                raise ValueError(f"Format non supporté: {format}")

            return result

        except Exception as e:
            return {"success": False, "error": str(e), "format": format}

    @staticmethod
    def get_supported_formats() -> List[str]:
        """Obtenir la liste des formats supportés"""
        return ["csv", "excel", "json"]

    @staticmethod
    def get_format_info(format: str) -> Dict[str, Any]:
        """Obtenir les informations sur un format"""
        formats_info = {
            "csv": {
                "name": "CSV",
                "description": "Fichier CSV séparé par virgules",
                "mime_type": "text/csv",
                "extension": ".csv",
            },
            "excel": {
                "name": "Excel",
                "description": "Fichier Excel (.xlsx)",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "extension": ".xlsx",
            },
            "json": {
                "name": "JSON",
                "description": "Fichier JSON structuré",
                "mime_type": "application/json",
                "extension": ".json",
            },
        }

        return formats_info.get(
            format.lower(),
            {
                "name": "Inconnu",
                "description": "Format non supporté",
                "mime_type": "application/octet-stream",
                "extension": "",
            },
        )
