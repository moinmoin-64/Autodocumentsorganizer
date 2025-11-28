#!/usr/bin/env python3
"""
Backup Script für Dokumentenverwaltung
Erstellt automatische Backups der Dokumente und Datenbank
"""

import os
import sys
import shutil
import tarfile
import logging
from pathlib import Path
from datetime import datetime
import yaml

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class BackupManager:
    """Verwaltet Backups des Systems"""
    
    def __init__(self, config_path='config.yaml'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.storage_path = Path(self.config['system']['storage']['base_path'])
        self.data_path = Path(self.config['system']['storage']['data_path'])
        self.db_path = Path(self.config['database']['path'])
        
        # Backup-Verzeichnis
        self.backup_dir = Path('/mnt/documents/backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, include_documents=True, include_database=True):
        """
        Erstellt vollständiges Backup
        
        Args:
            include_documents: Dokumente sichern
            include_database: Datenbank sichern
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"Erstelle Backup: {backup_name}")
        
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                
                # Datenbank
                if include_database and self.db_path.exists():
                    logger.info("Sichere Datenbank...")
                    tar.add(self.db_path, arcname="database.db")
                
                # CSV-Daten
                if self.data_path.exists():
                    logger.info("Sichere CSV-Daten...")
                    tar.add(self.data_path, arcname="data")
                
                # structure.json
                structure_file = self.storage_path.parent / 'structure.json'
                if structure_file.exists():
                    logger.info("Sichere structure.json...")
                    tar.add(structure_file, arcname="structure.json")
                
                # Dokumente (optional, kann groß sein)
                if include_documents and self.storage_path.exists():
                    logger.info("Sichere Dokumente (kann dauern)...")
                    tar.add(self.storage_path, arcname="storage")
            
            # Backup-Größe
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Backup erstellt: {backup_path}")
            logger.info(f"  Größe: {size_mb:.2f} MB")
            
            # Alte Backups löschen (behalte letzte 7)
            self.cleanup_old_backups(keep=7)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Fehler beim Backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def cleanup_old_backups(self, keep=7):
        """Löscht alte Backups, behält nur die letzten N"""
        backups = sorted(self.backup_dir.glob("backup_*.tar.gz"))
        
        if len(backups) > keep:
            to_delete = backups[:-keep]
            logger.info(f"Lösche {len(to_delete)} alte Backups...")
            
            for backup in to_delete:
                backup.unlink()
                logger.info(f"  Gelöscht: {backup.name}")
    
    def restore_backup(self, backup_path):
        """
        Stellt Backup wieder her
        
        Args:
            backup_path: Pfad zum Backup
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            logger.error(f"Backup nicht gefunden: {backup_path}")
            return False
        
        logger.warning("⚠️  ACHTUNG: Restore überschreibt existierende Daten!")
        confirm = input("Fortfahren? [j/N]: ")
        
        if confirm.lower() not in ['j', 'ja', 'y', 'yes']:
            logger.info("Restore abgebrochen")
            return False
        
        try:
            logger.info(f"Stelle wieder her: {backup_path.name}")
            
            with tarfile.open(backup_path, "r:gz") as tar:
                # Extrahiere in temp
                temp_dir = Path("/tmp/restore_temp")
                temp_dir.mkdir(exist_ok=True)
                
                tar.extractall(temp_dir)
                
                # Datenbank
                if (temp_dir / "database.db").exists():
                    logger.info("Restore Datenbank...")
                    shutil.copy2(temp_dir / "database.db", self.db_path)
                
                # CSV-Daten
                if (temp_dir / "data").exists():
                    logger.info("Restore CSV-Daten...")
                    if self.data_path.exists():
                        shutil.rmtree(self.data_path)
                    shutil.copytree(temp_dir / "data", self.data_path)
                
                # structure.json
                if (temp_dir / "structure.json").exists():
                    logger.info("Restore structure.json...")
                    shutil.copy2(
                        temp_dir / "structure.json",
                        self.storage_path.parent / "structure.json"
                    )
                
                # Dokumente
                if (temp_dir / "storage").exists():
                    logger.info("Restore Dokumente...")
                    if self.storage_path.exists():
                        shutil.rmtree(self.storage_path)
                    shutil.copytree(temp_dir / "storage", self.storage_path)
                
                # Cleanup
                shutil.rmtree(temp_dir)
                
            logger.info("✓ Restore erfolgreich!")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Restore: {e}")
            return False
    
    def list_backups(self):
        """Listet alle verfügbaren Backups"""
        backups = sorted(self.backup_dir.glob("backup_*.tar.gz"), reverse=True)
        
        if not backups:
            logger.info("Keine Backups gefunden")
            return []
        
        logger.info(f"Verfügbare Backups ({len(backups)}):")
        for backup in backups:
            size_mb = backup.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            logger.info(f"  - {backup.name} ({size_mb:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M')})")
        
        return backups


def main():
    """CLI Interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup Manager für Dokumentenverwaltung")
    parser.add_argument('command', choices=['create', 'restore', 'list'], 
                       help='Aktion: create, restore, list')
    parser.add_argument('--backup', help='Backup-Datei für restore')
    parser.add_argument('--no-docs', action='store_true', 
                       help='Keine Dokumente sichern (nur DB/CSV)')
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.command == 'create':
        include_docs = not args.no_docs
        manager.create_backup(include_documents=include_docs)
    
    elif args.command == 'restore':
        if not args.backup:
            logger.error("--backup Parameter erforderlich für restore")
            sys.exit(1)
        manager.restore_backup(args.backup)
    
    elif args.command == 'list':
        manager.list_backups()


if __name__ == "__main__":
    main()
