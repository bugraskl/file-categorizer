#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Categorizer - Undo Manager
Geri alma işlemlerini yöneten modül.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class UndoManager:
    """Geri alma işlemlerini yöneten sınıf"""
    
    def __init__(self, logs_path: str):
        self.logs_path = Path(logs_path)
        self.logs_path.mkdir(parents=True, exist_ok=True)
    
    def save_log(self, log_data: Dict) -> str:
        """
        İşlem logunu kaydet.
        
        Args:
            log_data: İşlem verileri
        
        Returns:
            Log dosyasının yolu
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"operation_{timestamp}.json"
        log_path = self.logs_path / log_filename
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        return str(log_path)
    
    def load_last_log(self) -> Optional[Dict]:
        """
        Son işlem logunu yükle.
        
        Returns:
            Log verileri veya None
        """
        log_files = sorted(
            self.logs_path.glob('operation_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not log_files:
            return None
        
        last_log = log_files[0]
        
        with open(last_log, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_log(self, log_path: str) -> Optional[Dict]:
        """
        Belirtilen log dosyasını yükle.
        
        Args:
            log_path: Log dosyasının yolu
        
        Returns:
            Log verileri veya None
        """
        path = Path(log_path)
        
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_all_logs(self) -> List[Dict]:
        """
        Tüm logları listele.
        
        Returns:
            Log listesi (özet bilgilerle)
        """
        logs = []
        
        for log_file in sorted(
            self.logs_path.glob('operation_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        ):
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logs.append({
                    'path': str(log_file),
                    'timestamp': data.get('timestamp'),
                    'folder': data.get('folder'),
                    'total_files': data.get('total_files', 0),
                    'modes': data.get('modes', [])
                })
        
        return logs
    
    def undo(self, log_path: str = None) -> Dict:
        """
        Son işlemi veya belirtilen işlemi geri al.
        
        Args:
            log_path: Geri alınacak log dosyasının yolu (opsiyonel)
        
        Returns:
            İşlem sonucu
        """
        # Log yükle
        if log_path:
            log_data = self.load_log(log_path)
        else:
            log_data = self.load_last_log()
        
        if not log_data:
            return {
                'success': False,
                'error': 'Geri alınacak işlem bulunamadı'
            }
        
        operations = log_data.get('operations', [])
        
        if not operations:
            return {
                'success': False,
                'error': 'İşlem listesi boş'
            }
        
        # Geri alma işlemi
        restored_files = 0
        errors = []
        affected_folders = set()
        
        # İşlemleri ters sırayla geri al
        for op in reversed(operations):
            old_path = Path(op['old_path'])
            new_path = Path(op['new_path'])
            
            try:
                if new_path.exists():
                    # Eski konuma geri taşı
                    shutil.move(str(new_path), str(old_path))
                    restored_files += 1
                    
                    # Etkilenen klasörü kaydet
                    affected_folders.add(new_path.parent)
                else:
                    errors.append(f"Dosya bulunamadı: {new_path}")
            except Exception as e:
                errors.append(f"Geri alma hatası: {new_path} - {e}")
        
        # Boş klasörleri temizle
        cleaned_folders = 0
        for folder in affected_folders:
            if self._cleanup_empty_folder(folder):
                cleaned_folders += 1
        
        # Log dosyasını sil (başarılı geri alma sonrası)
        if restored_files > 0:
            self._delete_log(log_data)
        
        return {
            'success': True,
            'restored_files': restored_files,
            'cleaned_folders': cleaned_folders,
            'errors': errors
        }
    
    def _cleanup_empty_folder(self, folder: Path) -> bool:
        """
        Boş klasörü temizle.
        
        Args:
            folder: Kontrol edilecek klasör
        
        Returns:
            Klasör silindi mi?
        """
        try:
            if folder.exists() and folder.is_dir():
                # Klasör boş mu kontrol et
                if not any(folder.iterdir()):
                    folder.rmdir()
                    return True
        except Exception:
            pass
        
        return False
    
    def _delete_log(self, log_data: Dict) -> bool:
        """
        İşlem tamamlandıktan sonra log dosyasını sil/arşivle.
        
        Args:
            log_data: Log verileri
        
        Returns:
            Silindi mi?
        """
        # Son log dosyasını bul
        log_files = sorted(
            self.logs_path.glob('operation_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if log_files:
            try:
                # Dosyayı "undone_" öneki ile yeniden adlandır (arşiv)
                last_log = log_files[0]
                archive_name = f"undone_{last_log.name}"
                archive_path = self.logs_path / archive_name
                last_log.rename(archive_path)
                return True
            except Exception:
                pass
        
        return False
    
    def clear_all_logs(self) -> Dict:
        """
        Tüm logları temizle.
        
        Returns:
            İşlem sonucu
        """
        deleted_count = 0
        
        for log_file in self.logs_path.glob('*.json'):
            try:
                log_file.unlink()
                deleted_count += 1
            except Exception:
                pass
        
        return {
            'success': True,
            'deleted_logs': deleted_count
        }


def test_undo_manager():
    """Test fonksiyonu"""
    import tempfile
    
    # Geçici dizin oluştur
    with tempfile.TemporaryDirectory() as temp_dir:
        logs_path = Path(temp_dir) / 'logs'
        manager = UndoManager(str(logs_path))
        
        # Test logu oluştur
        test_log = {
            'timestamp': datetime.now().isoformat(),
            'folder': '/test/folder',
            'modes': ['extension', 'size'],
            'total_files': 5,
            'operations': [
                {'old_path': '/test/file1.txt', 'new_path': '/test/TXT/file1.txt'},
                {'old_path': '/test/file2.pdf', 'new_path': '/test/PDF/file2.pdf'},
            ],
            'errors': []
        }
        
        # Log kaydet
        log_path = manager.save_log(test_log)
        print(f"Log kaydedildi: {log_path}")
        
        # Son logu yükle
        loaded = manager.load_last_log()
        print(f"Yüklenen log: {loaded['timestamp']}")
        
        # Tüm logları listele
        all_logs = manager.get_all_logs()
        print(f"Toplam log sayısı: {len(all_logs)}")
        
        print("\nTest başarılı!")


if __name__ == '__main__':
    test_undo_manager()
