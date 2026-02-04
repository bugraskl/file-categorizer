#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Categorizer - Main Categorization Engine
Dosyaları çeşitli kurallara göre kategorize eden ana motor.
"""

import os
import sys
import json
import argparse
import shutil
import mimetypes
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

# Local imports
from similarity import SimilarityAnalyzer
from undo_manager import UndoManager
from utils import (
    get_mime_category, 
    get_size_category, 
    format_date,
    generate_unique_name,
    calculate_dynamic_size_buckets,
    get_file_info,
    progress_update,
    get_localized_name
)


class FileCategorizer:
    """Main file categorization class"""
    
    # Bilingual pattern mappings
    DEFAULT_PATTERNS = {
        'en': {
            r'(?i).*invoice.*': 'Invoices',
            r'(?i).*receipt.*': 'Receipts',
            r'(?i).*report.*': 'Reports',
            r'(?i)^IMG_.*': 'Camera_Photos',
            r'(?i)^VID_.*': 'Video_Recordings',
            r'(?i)^DSC_.*': 'Camera_Photos',
            r'(?i)^DCIM.*': 'Camera_Photos',
            r'(?i).*screenshot.*': 'Screenshots',
            r'(?i).*backup.*': 'Backups',
            r'(?i).*download.*': 'Downloads',
            r'(?i).*temp.*': 'Temporary_Files',
        },
        'tr': {
            r'(?i).*invoice.*': 'Faturalar',
            r'(?i).*fatura.*': 'Faturalar',
            r'(?i).*receipt.*': 'Makbuzlar',
            r'(?i).*makbuz.*': 'Makbuzlar',
            r'(?i).*report.*': 'Raporlar',
            r'(?i).*rapor.*': 'Raporlar',
            r'(?i)^IMG_.*': 'Kamera_Cekimleri',
            r'(?i)^VID_.*': 'Video_Kayitlari',
            r'(?i)^DSC_.*': 'Kamera_Cekimleri',
            r'(?i)^DCIM.*': 'Kamera_Cekimleri',
            r'(?i).*screenshot.*': 'Ekran_Goruntuleri',
            r'(?i).*ekran.*': 'Ekran_Goruntuleri',
            r'(?i).*backup.*': 'Yedekler',
            r'(?i).*yedek.*': 'Yedekler',
            r'(?i).*download.*': 'Indirilenler',
            r'(?i).*temp.*': 'Gecici_Dosyalar',
        }
    }
    
    # Boyut aralıkları (bytes)
    SIZE_RANGES = [
        (0, 1024 * 1024, '0-1MB'),
        (1024 * 1024, 10 * 1024 * 1024, '1-10MB'),
        (10 * 1024 * 1024, 100 * 1024 * 1024, '10-100MB'),
        (100 * 1024 * 1024, 1024 * 1024 * 1024, '100MB-1GB'),
        (1024 * 1024 * 1024, float('inf'), '1GB+'),
    ]
    
    def __init__(self, folder_path: str, logs_path: str = None, language: str = 'en'):
        self.folder_path = Path(folder_path)
        self.logs_path = Path(logs_path) if logs_path else Path(__file__).parent.parent.parent / 'logs'
        self.language = language
        self.files: List[Dict] = []
        self.plan: Dict[str, List[Dict]] = defaultdict(list)
        self.similarity_analyzer = SimilarityAnalyzer()
        self.undo_manager = UndoManager(self.logs_path)
        
    def scan_folder(self) -> Dict:
        """Klasörü tarar ve dosya bilgilerini toplar"""
        self.files = []
        total_size = 0
        
        try:
            all_files = list(self.folder_path.iterdir())
            total_count = len([f for f in all_files if f.is_file()])
            
            for i, item in enumerate(all_files):
                if item.is_file():
                    try:
                        file_info = get_file_info(item)
                        self.files.append(file_info)
                        total_size += file_info['size']
                        
                        if i % 10 == 0:
                            progress_update(
                                percent=int((i / len(all_files)) * 100),
                                message=f"Taranıyor: {i}/{total_count} dosya",
                                detail=item.name[:50]
                            )
                    except Exception as e:
                        print(f"Dosya okuma hatası: {item} - {e}", file=sys.stderr)
            
            return {
                'success': True,
                'total_files': len(self.files),
                'total_size': total_size,
                'folder': str(self.folder_path)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def categorize_by_extension(self) -> Dict[str, List[Dict]]:
        """Dosya uzantısına göre kategorileştir"""
        result = defaultdict(list)
        for file in self.files:
            ext = file['extension'].lower().lstrip('.') or 'no_extension'
            folder_name = ext.upper()
            result[folder_name].append(file)
        return dict(result)
    
    def categorize_by_mime(self) -> Dict[str, List[Dict]]:
        """Categorize by MIME type"""
        result = defaultdict(list)
        for file in self.files:
            category = get_mime_category(file['mime_type'], self.language)
            result[category].append(file)
        return dict(result)
    
    def categorize_by_creation_date(self, date_format: str = 'YYYY') -> Dict[str, List[Dict]]:
        """Oluşturma tarihine göre kategorileştir"""
        result = defaultdict(list)
        for file in self.files:
            folder_name = format_date(file['created'], date_format)
            result[folder_name].append(file)
        return dict(result)
    
    def categorize_by_modification_date(self, date_format: str = 'YYYY') -> Dict[str, List[Dict]]:
        """Değiştirilme tarihine göre kategorileştir"""
        result = defaultdict(list)
        for file in self.files:
            folder_name = format_date(file['modified'], date_format)
            result[folder_name].append(file)
        return dict(result)
    
    def categorize_by_size(self) -> Dict[str, List[Dict]]:
        """Dosya boyutuna göre kategorileştir"""
        result = defaultdict(list)
        for file in self.files:
            category = get_size_category(file['size'], self.SIZE_RANGES)
            result[category].append(file)
        return dict(result)
    
    def categorize_by_pattern(self, custom_patterns: Dict[str, str] = None) -> Dict[str, List[Dict]]:
        """Categorize by name pattern"""
        patterns = dict(self.DEFAULT_PATTERNS.get(self.language, self.DEFAULT_PATTERNS['en']))
        
        # Add custom patterns
        if custom_patterns:
            for pattern, folder in custom_patterns.items():
                regex_pattern = pattern.replace('*', '.*').replace('?', '.')
                patterns[f'(?i){regex_pattern}'] = folder
        
        result = defaultdict(list)
        unmatched = []
        other_name = 'Other' if self.language == 'en' else 'Diger'
        
        for file in self.files:
            matched = False
            for pattern, folder in patterns.items():
                if re.match(pattern, file['name']):
                    result[folder].append(file)
                    matched = True
                    break
            
            if not matched:
                unmatched.append(file)
        
        if unmatched:
            result[other_name].extend(unmatched)
        
        return dict(result)
    
    def categorize_by_similarity(self, threshold: float = 0.8) -> Dict[str, List[Dict]]:
        """Dosya ismi benzerliğine göre grupla"""
        file_names = [f['name_without_ext'] for f in self.files]
        groups = self.similarity_analyzer.group_by_similarity(file_names, threshold)
        
        result = defaultdict(list)
        file_map = {f['name_without_ext']: f for f in self.files}
        
        for group_name, members in groups.items():
            for member in members:
                if member in file_map:
                    result[group_name].append(file_map[member])
        
        return dict(result)
    
    def categorize_by_dynamic_size(self) -> Dict[str, List[Dict]]:
        """Dinamik boyut histogramı ile kategorileştir"""
        sizes = [f['size'] for f in self.files]
        buckets = calculate_dynamic_size_buckets(sizes)
        
        result = defaultdict(list)
        for file in self.files:
            for bucket_name, (min_size, max_size) in buckets.items():
                if min_size <= file['size'] < max_size:
                    result[bucket_name].append(file)
                    break
        
        return dict(result)
    
    def categorize_by_same_name(self) -> Dict[str, List[Dict]]:
        """Group same-name files (different extensions)"""
        result = defaultdict(list)
        
        for file in self.files:
            folder_name = file['name_without_ext']
            result[folder_name].append(file)
        
        # Keep only groups with multiple files
        final_result = {}
        single_files = []
        single_name = 'Single_Files' if self.language == 'en' else 'Tekil_Dosyalar'
        
        for folder, files in result.items():
            if len(files) > 1:
                final_result[folder] = files
            else:
                single_files.extend(files)
        
        if single_files:
            final_result[single_name] = single_files
        
        return final_result
    
    def categorize_by_multi_criteria(self, criteria1: str, criteria2: str, 
                                      operator: str = 'AND', options: Dict = None) -> Dict[str, List[Dict]]:
        """Çoklu kritere göre kategorileştir"""
        options = options or {}
        
        # İlk kritere göre kategorileştir
        cat1_result = self._apply_single_criteria(criteria1, options)
        
        if operator == 'AND':
            # Her dosyayı her iki kritere göre kategorileştir
            result = defaultdict(list)
            for file in self.files:
                cat1 = self._get_file_category(file, criteria1, options)
                cat2 = self._get_file_category(file, criteria2, options)
                folder_name = f"{cat1}_{cat2}"
                result[folder_name].append(file)
            return dict(result)
        else:  # OR
            # Her iki kriterin sonuçlarını birleştir
            cat2_result = self._apply_single_criteria(criteria2, options)
            result = defaultdict(list)
            
            for folder, files in cat1_result.items():
                result[f"{criteria1}_{folder}"].extend(files)
            for folder, files in cat2_result.items():
                result[f"{criteria2}_{folder}"].extend(files)
            
            return dict(result)
    
    def _apply_single_criteria(self, criteria: str, options: Dict) -> Dict[str, List[Dict]]:
        """Tek kriter uygula"""
        date_format = options.get('dateFormat', 'YYYY')
        
        if criteria == 'extension':
            return self.categorize_by_extension()
        elif criteria == 'mime':
            return self.categorize_by_mime()
        elif criteria == 'size':
            return self.categorize_by_size()
        elif criteria == 'year':
            return self.categorize_by_creation_date('YYYY')
        elif criteria == 'month':
            return self.categorize_by_creation_date('YYYY-MM')
        else:
            return {}
    
    def _get_file_category(self, file: Dict, criteria: str, options: Dict) -> str:
        """Get category for a single file"""
        date_format = options.get('dateFormat', 'YYYY')
        
        if criteria == 'extension':
            return file['extension'].upper().lstrip('.') or 'NO_EXT'
        elif criteria == 'mime':
            return get_mime_category(file['mime_type'], self.language)
        elif criteria == 'size':
            return get_size_category(file['size'], self.SIZE_RANGES)
        elif criteria == 'year':
            return format_date(file['created'], 'YYYY')
        elif criteria == 'month':
            return format_date(file['created'], 'YYYY-MM')
        else:
            return 'Other' if self.language == 'en' else 'Diger'
    
    def generate_plan(self, modes: List[str], options: Dict = None) -> Dict:
        """Taşıma planı oluştur"""
        options = options or {}
        self.plan = defaultdict(list)
        
        if not self.files:
            self.scan_folder()
        
        total_modes = len(modes)
        
        for i, mode in enumerate(modes):
            progress_update(
                percent=int((i / total_modes) * 50),
                message=f"Plan oluşturuluyor: {mode}",
                detail=f"Mod {i + 1}/{total_modes}"
            )
            
            if mode == 'extension':
                result = self.categorize_by_extension()
            elif mode == 'mime':
                result = self.categorize_by_mime()
            elif mode == 'creation_date':
                result = self.categorize_by_creation_date(options.get('dateFormat', 'YYYY'))
            elif mode == 'modification_date':
                result = self.categorize_by_modification_date(options.get('dateFormat', 'YYYY'))
            elif mode == 'size':
                result = self.categorize_by_size()
            elif mode == 'pattern':
                custom_patterns = {}
                for p in options.get('patterns', []):
                    custom_patterns[p['pattern']] = p['folder']
                result = self.categorize_by_pattern(custom_patterns)
            elif mode == 'similarity':
                threshold = options.get('similarityThreshold', 80) / 100
                result = self.categorize_by_similarity(threshold)
            elif mode == 'dynamic_size':
                result = self.categorize_by_dynamic_size()
            elif mode == 'same_name':
                result = self.categorize_by_same_name()
            elif mode == 'multi_criteria':
                mc = options.get('multiCriteria', {})
                result = self.categorize_by_multi_criteria(
                    mc.get('criteria1', 'extension'),
                    mc.get('criteria2', 'year'),
                    mc.get('operator', 'AND'),
                    options
                )
            else:
                continue
            
            # Sonuçları birleştir
            for folder, files in result.items():
                for file in files:
                    # Dosya zaten planda varsa atla
                    if not any(f['path'] == file['path'] for f in self.plan[folder]):
                        self.plan[folder].append(file)
        
        # Plan özeti
        plan_summary = {}
        for folder, files in self.plan.items():
            plan_summary[folder] = [f['name'] for f in files]
        
        return {
            'success': True,
            'total_files': sum(len(files) for files in self.plan.values()),
            'plan': plan_summary
        }
    
    def simulate(self, modes: List[str], options: Dict = None) -> Dict:
        """Simülasyon modu - dosyaları taşımadan planı göster"""
        return self.generate_plan(modes, options)
    
    def execute(self, modes: List[str], options: Dict = None) -> Dict:
        """Taşıma işlemini gerçekleştir"""
        options = options or {}
        conflict_resolution = options.get('conflictResolution', 'number')
        
        # Plan oluştur
        plan_result = self.generate_plan(modes, options)
        if not plan_result['success']:
            return plan_result
        
        # İşlem kaydı
        operations = []
        errors = []
        folder_breakdown = {}
        start_time = datetime.now()
        
        total_files = sum(len(files) for files in self.plan.values())
        processed = 0
        
        for folder_name, files in self.plan.items():
            # Klasör oluştur
            target_folder = self.folder_path / folder_name
            try:
                target_folder.mkdir(exist_ok=True)
            except Exception as e:
                errors.append(f"Klasör oluşturulamadı: {folder_name} - {e}")
                continue
            
            folder_breakdown[folder_name] = 0
            
            for file in files:
                processed += 1
                progress_update(
                    percent=50 + int((processed / total_files) * 50),
                    message=f"Taşınıyor: {processed}/{total_files}",
                    detail=file['name'][:50]
                )
                
                source_path = Path(file['path'])
                target_path = target_folder / file['name']
                
                # İsim çakışması kontrolü
                if target_path.exists():
                    target_path = generate_unique_name(target_path, conflict_resolution)
                
                try:
                    shutil.move(str(source_path), str(target_path))
                    operations.append({
                        'old_path': str(source_path),
                        'new_path': str(target_path)
                    })
                    folder_breakdown[folder_name] += 1
                except Exception as e:
                    errors.append(f"Taşıma hatası: {file['name']} - {e}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # İşlem logunu kaydet
        if operations:
            log_data = {
                'timestamp': start_time.isoformat(),
                'folder': str(self.folder_path),
                'modes': modes,
                'options': options,
                'total_files': len(operations),
                'operations': operations,
                'errors': errors
            }
            self.undo_manager.save_log(log_data)
        
        return {
            'success': True,
            'total_files': total_files,
            'moved_files': len(operations),
            'folders_created': len(folder_breakdown),
            'folder_breakdown': folder_breakdown,
            'errors': errors,
            'duration': duration
        }
    
    def undo(self) -> Dict:
        """Son işlemi geri al"""
        return self.undo_manager.undo()


def main():
    """Ana giriş noktası"""
    parser = argparse.ArgumentParser(description='File Categorizer')
    parser.add_argument('--scan', type=str, help='Taranacak klasör yolu')
    parser.add_argument('--simulate', action='store_true', help='Simülasyon modu')
    parser.add_argument('--execute', action='store_true', help='Gerçek taşıma')
    parser.add_argument('--undo', action='store_true', help='Son işlemi geri al')
    parser.add_argument('--folder', type=str, help='Hedef klasör')
    parser.add_argument('--modes', type=str, help='Kategorileştirme modları (JSON)')
    parser.add_argument('--options', type=str, help='Gelişmiş seçenekler (JSON)')
    parser.add_argument('--logs-path', type=str, help='Log klasörü yolu')
    parser.add_argument('--test', action='store_true', help='Test modu')
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        print(json.dumps({'success': True, 'message': 'Test successful'}))
        return
    
    # Folder scan
    if args.scan:
        categorizer = FileCategorizer(args.scan, args.logs_path)
        result = categorizer.scan_folder()
        print('RESULT:' + json.dumps(result, ensure_ascii=False))
        return
    
    # Simulation
    if args.simulate and args.folder:
        modes = json.loads(args.modes) if args.modes else []
        options = json.loads(args.options) if args.options else {}
        language = options.get('language', 'en')
        
        categorizer = FileCategorizer(args.folder, args.logs_path, language)
        result = categorizer.simulate(modes, options)
        print('RESULT:' + json.dumps(result, ensure_ascii=False))
        return
    
    # Execute
    if args.execute and args.folder:
        modes = json.loads(args.modes) if args.modes else []
        options = json.loads(args.options) if args.options else {}
        language = options.get('language', 'en')
        
        categorizer = FileCategorizer(args.folder, args.logs_path, language)
        result = categorizer.execute(modes, options)
        print('RESULT:' + json.dumps(result, ensure_ascii=False))
        return
    
    # Undo
    if args.undo:
        categorizer = FileCategorizer('.', args.logs_path)
        result = categorizer.undo()
        print('RESULT:' + json.dumps(result, ensure_ascii=False))
        return
    
    parser.print_help()


if __name__ == '__main__':
    main()
