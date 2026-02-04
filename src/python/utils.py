#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Categorizer - Utility Functions
Helper functions and constants with bilingual support.
"""

import os
import sys
import json
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math


# Bilingual MIME category mappings
MIME_CATEGORIES = {
    'en': {
        'image': 'Images',
        'video': 'Videos',
        'audio': 'Audio_Files',
        'text': 'Text_Files',
        'application/pdf': 'PDF_Documents',
        'application/msword': 'Word_Documents',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word_Documents',
        'application/vnd.ms-excel': 'Excel_Spreadsheets',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel_Spreadsheets',
        'application/vnd.ms-powerpoint': 'PowerPoint_Presentations',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PowerPoint_Presentations',
        'application/zip': 'Archives',
        'application/x-rar-compressed': 'Archives',
        'application/x-7z-compressed': 'Archives',
        'application/x-tar': 'Archives',
        'application/gzip': 'Archives',
        'application/json': 'Data_Files',
        'application/xml': 'Data_Files',
        'application/javascript': 'Code_Files',
        'text/html': 'Web_Files',
        'text/css': 'Web_Files',
        'text/javascript': 'Code_Files',
        'text/x-python': 'Code_Files',
        '_default': 'Other',
        '_date_unknown': 'Date_Unknown',
        '_all_files': 'All_Files',
        '_too_large': 'Very_Large',
        '_folder': 'Folder'
    },
    'tr': {
        'image': 'Resimler',
        'video': 'Videolar',
        'audio': 'Ses_Dosyalari',
        'text': 'Metin_Dosyalari',
        'application/pdf': 'PDF_Belgeler',
        'application/msword': 'Word_Belgeler',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word_Belgeler',
        'application/vnd.ms-excel': 'Excel_Tablolar',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel_Tablolar',
        'application/vnd.ms-powerpoint': 'PowerPoint_Sunumlar',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PowerPoint_Sunumlar',
        'application/zip': 'Arsivler',
        'application/x-rar-compressed': 'Arsivler',
        'application/x-7z-compressed': 'Arsivler',
        'application/x-tar': 'Arsivler',
        'application/gzip': 'Arsivler',
        'application/json': 'Veri_Dosyalari',
        'application/xml': 'Veri_Dosyalari',
        'application/javascript': 'Kod_Dosyalari',
        'text/html': 'Web_Dosyalari',
        'text/css': 'Web_Dosyalari',
        'text/javascript': 'Kod_Dosyalari',
        'text/x-python': 'Kod_Dosyalari',
        '_default': 'Diger',
        '_date_unknown': 'Tarih_Belirsiz',
        '_all_files': 'Tum_Dosyalar',
        '_too_large': 'Cok_Buyuk',
        '_folder': 'Klasor'
    }
}


def get_mime_type(filepath: Path) -> str:
    """
    Get the MIME type of a file.
    
    Args:
        filepath: File path
    
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(str(filepath))
    return mime_type or 'application/octet-stream'


def get_mime_category(mime_type: str, lang: str = 'en') -> str:
    """
    Return category name based on MIME type.
    
    Args:
        mime_type: MIME type
        lang: Language code ('en' or 'tr')
    
    Returns:
        Category name
    """
    categories = MIME_CATEGORIES.get(lang, MIME_CATEGORIES['en'])
    
    if not mime_type:
        return categories['_default']
    
    # Exact match check
    if mime_type in categories:
        return categories[mime_type]
    
    # Main type check (image/jpeg -> image)
    main_type = mime_type.split('/')[0]
    if main_type in categories:
        return categories[main_type]
    
    return categories['_default']


def get_localized_name(key: str, lang: str = 'en') -> str:
    """
    Get localized name for special folder names.
    
    Args:
        key: Key name (e.g., '_default', '_date_unknown')
        lang: Language code
    
    Returns:
        Localized name
    """
    categories = MIME_CATEGORIES.get(lang, MIME_CATEGORIES['en'])
    return categories.get(key, key)


def get_size_category(size: int, ranges: List[Tuple[int, int, str]]) -> str:
    """
    Return category name based on file size.
    
    Args:
        size: File size (bytes)
        ranges: Size ranges list [(min, max, name), ...]
    
    Returns:
        Category name
    """
    for min_size, max_size, category_name in ranges:
        if min_size <= size < max_size:
            return category_name
    return 'Very_Large'


def format_date(timestamp: float, date_format: str = 'YYYY') -> str:
    """
    Timestamp'i belirtilen formatta tarihe dönüştür.
    
    Args:
        timestamp: Unix timestamp
        date_format: 'YYYY', 'YYYY-MM' veya 'YYYY-MM-DD'
    
    Returns:
        Formatlanmış tarih string'i
    """
    try:
        dt = datetime.fromtimestamp(timestamp)
        
        if date_format == 'YYYY':
            return str(dt.year)
        elif date_format == 'YYYY-MM':
            return f"{dt.year}-{dt.month:02d}"
        elif date_format == 'YYYY-MM-DD':
            return f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
        else:
            return str(dt.year)
    except Exception:
        return 'Tarih_Belirsiz'


def generate_unique_name(filepath: Path, method: str = 'number') -> Path:
    """
    Çakışma durumunda benzersiz dosya adı oluştur.
    
    Args:
        filepath: Orijinal dosya yolu
        method: 'number' veya 'timestamp'
    
    Returns:
        Benzersiz dosya yolu
    """
    if not filepath.exists():
        return filepath
    
    parent = filepath.parent
    stem = filepath.stem
    suffix = filepath.suffix
    
    if method == 'timestamp':
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{stem}_{timestamp}{suffix}"
        return parent / new_name
    else:  # number
        counter = 1
        while True:
            new_name = f"{stem} ({counter}){suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
            if counter > 1000:  # Sonsuz döngü koruması
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                return parent / f"{stem}_{timestamp}{suffix}"


def calculate_dynamic_size_buckets(sizes: List[int], num_buckets: int = 5) -> Dict[str, Tuple[int, int]]:
    """
    Veriye göre dinamik boyut aralıkları hesapla.
    
    Args:
        sizes: Dosya boyutları listesi
        num_buckets: Oluşturulacak aralık sayısı
    
    Returns:
        Aralık adı -> (min, max) eşleştirmesi
    """
    if not sizes:
        return {'Tum_Dosyalar': (0, float('inf'))}
    
    sizes = sorted(sizes)
    total = len(sizes)
    
    if total < num_buckets:
        num_buckets = max(1, total)
    
    buckets = {}
    bucket_size = total // num_buckets
    
    for i in range(num_buckets):
        start_idx = i * bucket_size
        if i == num_buckets - 1:
            end_idx = total - 1
        else:
            end_idx = (i + 1) * bucket_size - 1
        
        min_size = sizes[start_idx]
        max_size = sizes[end_idx] if i == num_buckets - 1 else sizes[end_idx + 1]
        
        # Okunabilir aralık adı
        min_str = format_size_short(min_size)
        max_str = format_size_short(max_size)
        bucket_name = f"{min_str}-{max_str}"
        
        buckets[bucket_name] = (min_size, max_size + 1 if i == num_buckets - 1 else max_size)
    
    return buckets


def format_size_short(size: int) -> str:
    """
    Boyutu kısa formatta göster.
    
    Args:
        size: Boyut (bytes)
    
    Returns:
        Formatlanmış string (örn: "1.5MB")
    """
    if size == 0:
        return "0B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size, 1024)))
    i = min(i, len(units) - 1)
    
    value = size / (1024 ** i)
    
    if value >= 100:
        return f"{int(value)}{units[i]}"
    elif value >= 10:
        return f"{value:.1f}{units[i]}"
    else:
        return f"{value:.2f}{units[i]}"


def get_file_info(filepath: Path) -> Dict:
    """
    Dosya bilgilerini topla.
    
    Args:
        filepath: Dosya yolu
    
    Returns:
        Dosya bilgileri sözlüğü
    """
    stat = filepath.stat()
    
    return {
        'path': str(filepath),
        'name': filepath.name,
        'name_without_ext': filepath.stem,
        'extension': filepath.suffix,
        'size': stat.st_size,
        'created': stat.st_ctime,
        'modified': stat.st_mtime,
        'accessed': stat.st_atime,
        'mime_type': get_mime_type(filepath)
    }


def progress_update(percent: int = None, message: str = None, detail: str = None):
    """
    İlerleme güncellemesi gönder.
    
    Args:
        percent: İlerleme yüzdesi (0-100)
        message: Ana mesaj
        detail: Detay metni
    """
    update = {}
    
    if percent is not None:
        update['percent'] = percent
    if message is not None:
        update['message'] = message
    if detail is not None:
        update['detail'] = detail
    
    if update:
        print(f"PROGRESS:{json.dumps(update, ensure_ascii=False)}", flush=True)


def sanitize_folder_name(name: str) -> str:
    """
    Klasör adını dosya sistemi için temizle.
    
    Args:
        name: Orijinal klasör adı
    
    Returns:
        Temizlenmiş klasör adı
    """
    # Geçersiz karakterleri değiştir
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Boşlukları alt çizgi yap
    name = name.replace(' ', '_')
    
    # Ardışık alt çizgileri tek yap
    while '__' in name:
        name = name.replace('__', '_')
    
    # Başı ve sonundaki alt çizgileri kaldır
    name = name.strip('_.')
    
    # Maksimum uzunluk (Windows limiti: 255)
    if len(name) > 200:
        name = name[:200]
    
    # Boş kalırsa varsayılan ad
    return name or 'Klasor'


def format_bytes(size: int) -> str:
    """
    Boyutu okunabilir formatta göster.
    
    Args:
        size: Boyut (bytes)
    
    Returns:
        Formatlanmış string (örn: "1.50 MB")
    """
    if size == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = int(math.floor(math.log(size, 1024)))
    i = min(i, len(units) - 1)
    
    value = size / (1024 ** i)
    return f"{value:.2f} {units[i]}"


def count_files_by_extension(folder: Path) -> Dict[str, int]:
    """
    Klasördeki dosyaları uzantıya göre say.
    
    Args:
        folder: Klasör yolu
    
    Returns:
        Uzantı -> sayı eşleştirmesi
    """
    counts = {}
    
    for item in folder.iterdir():
        if item.is_file():
            ext = item.suffix.lower() or '.no_ext'
            counts[ext] = counts.get(ext, 0) + 1
    
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def get_folder_statistics(folder: Path) -> Dict:
    """
    Klasör istatistiklerini topla.
    
    Args:
        folder: Klasör yolu
    
    Returns:
        İstatistik sözlüğü
    """
    total_size = 0
    file_count = 0
    folder_count = 0
    extension_counts = {}
    size_breakdown = {
        'tiny': 0,      # < 1KB
        'small': 0,     # 1KB - 1MB
        'medium': 0,    # 1MB - 100MB
        'large': 0,     # 100MB - 1GB
        'huge': 0       # > 1GB
    }
    
    for item in folder.iterdir():
        if item.is_file():
            file_count += 1
            size = item.stat().st_size
            total_size += size
            
            # Uzantı sayacı
            ext = item.suffix.lower() or '.no_ext'
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
            
            # Boyut dağılımı
            if size < 1024:
                size_breakdown['tiny'] += 1
            elif size < 1024 * 1024:
                size_breakdown['small'] += 1
            elif size < 100 * 1024 * 1024:
                size_breakdown['medium'] += 1
            elif size < 1024 * 1024 * 1024:
                size_breakdown['large'] += 1
            else:
                size_breakdown['huge'] += 1
        
        elif item.is_dir():
            folder_count += 1
    
    return {
        'total_files': file_count,
        'total_folders': folder_count,
        'total_size': total_size,
        'total_size_formatted': format_bytes(total_size),
        'extension_counts': extension_counts,
        'size_breakdown': size_breakdown
    }


if __name__ == '__main__':
    # Test
    print("Utility Functions Test")
    print("=" * 40)
    
    # MIME testi
    print("\nMIME Kategorileri:")
    test_mimes = ['image/jpeg', 'video/mp4', 'application/pdf', 'text/plain', 'application/octet-stream']
    for mime in test_mimes:
        print(f"  {mime} -> {get_mime_category(mime)}")
    
    # Boyut formatlama testi
    print("\nBoyut Formatlama:")
    test_sizes = [0, 512, 1024, 1536000, 1073741824, 5368709120]
    for size in test_sizes:
        print(f"  {size} bytes -> {format_bytes(size)}")
    
    # Tarih formatlama testi
    print("\nTarih Formatlama:")
    now = datetime.now().timestamp()
    for fmt in ['YYYY', 'YYYY-MM', 'YYYY-MM-DD']:
        print(f"  {fmt} -> {format_date(now, fmt)}")
    
    print("\nTest tamamlandı!")
