#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Categorizer - Similarity Algorithms
Dosya ismi benzerlik algoritmaları: Levenshtein, Jaro-Winkler, LCS
"""

from typing import List, Dict, Tuple
from collections import defaultdict


class SimilarityAnalyzer:
    """Dosya ismi benzerlik analizi sınıfı"""
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        İki string arasındaki Levenshtein (edit) mesafesini hesaplar.
        Düşük değer = daha benzer
        """
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Ekleme, silme veya değiştirme maliyeti
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def levenshtein_similarity(self, s1: str, s2: str) -> float:
        """
        Levenshtein mesafesinden benzerlik oranı hesaplar.
        0.0 = tamamen farklı, 1.0 = aynı
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        distance = self.levenshtein_distance(s1.lower(), s2.lower())
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)
    
    def jaro_similarity(self, s1: str, s2: str) -> float:
        """
        İki string arasındaki Jaro benzerliğini hesaplar.
        0.0 = tamamen farklı, 1.0 = aynı
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        s1 = s1.lower()
        s2 = s2.lower()
        
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        
        # Eşleşme penceresi
        match_distance = max(len1, len2) // 2 - 1
        if match_distance < 0:
            match_distance = 0
        
        s1_matches = [False] * len1
        s2_matches = [False] * len2
        
        matches = 0
        transpositions = 0
        
        # Eşleşmeleri bul
        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)
            
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # Yer değiştirmeleri say
        k = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        
        jaro = (matches / len1 + matches / len2 + 
                (matches - transpositions / 2) / matches) / 3
        
        return jaro
    
    def jaro_winkler_similarity(self, s1: str, s2: str, p: float = 0.1) -> float:
        """
        İki string arasındaki Jaro-Winkler benzerliğini hesaplar.
        Ortak ön ek için bonus verir.
        0.0 = tamamen farklı, 1.0 = aynı
        """
        jaro = self.jaro_similarity(s1, s2)
        
        s1 = s1.lower()
        s2 = s2.lower()
        
        # Ortak ön ek (max 4 karakter)
        prefix_len = 0
        for i in range(min(len(s1), len(s2), 4)):
            if s1[i] == s2[i]:
                prefix_len += 1
            else:
                break
        
        return jaro + prefix_len * p * (1 - jaro)
    
    def longest_common_substring(self, s1: str, s2: str) -> Tuple[str, int]:
        """
        En uzun ortak alt dizeyi bulur.
        Returns: (ortak dize, uzunluk)
        """
        if not s1 or not s2:
            return '', 0
        
        s1 = s1.lower()
        s2 = s2.lower()
        
        m, n = len(s1), len(s2)
        
        # DP tablosu
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        max_length = 0
        end_index = 0
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    if dp[i][j] > max_length:
                        max_length = dp[i][j]
                        end_index = i
        
        lcs = s1[end_index - max_length:end_index]
        return lcs, max_length
    
    def lcs_similarity(self, s1: str, s2: str) -> float:
        """
        En uzun ortak alt dize uzunluğundan benzerlik oranı hesaplar.
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        _, lcs_length = self.longest_common_substring(s1, s2)
        max_len = max(len(s1), len(s2))
        return lcs_length / max_len
    
    def combined_similarity(self, s1: str, s2: str, 
                           levenshtein_weight: float = 0.3,
                           jaro_winkler_weight: float = 0.4,
                           lcs_weight: float = 0.3) -> float:
        """
        Tüm algoritmaların ağırlıklı ortalaması ile benzerlik hesaplar.
        """
        lev = self.levenshtein_similarity(s1, s2)
        jw = self.jaro_winkler_similarity(s1, s2)
        lcs = self.lcs_similarity(s1, s2)
        
        return (lev * levenshtein_weight + 
                jw * jaro_winkler_weight + 
                lcs * lcs_weight)
    
    def group_by_similarity(self, names: List[str], threshold: float = 0.8) -> Dict[str, List[str]]:
        """
        Benzer isimleri gruplar.
        
        Args:
            names: Dosya isimleri listesi
            threshold: Benzerlik eşiği (0.0 - 1.0)
        
        Returns:
            Grup adı -> dosya isimleri eşleştirmesi
        """
        if not names:
            return {}
        
        groups = defaultdict(list)
        used = set()
        
        # Her isim için en benzer grubu bul veya yeni grup oluştur
        for name in names:
            if name in used:
                continue
            
            # Bu isimle benzer isimleri bul
            similar_names = [name]
            used.add(name)
            
            for other_name in names:
                if other_name in used:
                    continue
                
                similarity = self.combined_similarity(name, other_name)
                
                if similarity >= threshold:
                    similar_names.append(other_name)
                    used.add(other_name)
            
            # Grup adını belirle (en kısa ortak ön ek veya ilk isim)
            group_name = self._find_common_prefix(similar_names)
            if not group_name or len(group_name) < 3:
                group_name = similar_names[0]
            
            # Grup adını temizle
            group_name = self._sanitize_group_name(group_name)
            
            groups[group_name].extend(similar_names)
        
        return dict(groups)
    
    def _find_common_prefix(self, names: List[str]) -> str:
        """İsimler arasındaki ortak ön eki bulur"""
        if not names:
            return ''
        if len(names) == 1:
            return names[0]
        
        sorted_names = sorted(names)
        first = sorted_names[0]
        last = sorted_names[-1]
        
        prefix = ''
        for i in range(min(len(first), len(last))):
            if first[i].lower() == last[i].lower():
                prefix += first[i]
            else:
                break
        
        # Kelime sınırında kes
        if '_' in prefix:
            prefix = '_'.join(prefix.split('_')[:-1]) + '_'
        elif '-' in prefix:
            prefix = '-'.join(prefix.split('-')[:-1]) + '-'
        
        return prefix.rstrip('_- ')
    
    def _sanitize_group_name(self, name: str) -> str:
        """Grup adını dosya sistemi için temizler"""
        # Geçersiz karakterleri kaldır
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Boşlukları alt çizgi yap
        name = name.replace(' ', '_')
        
        # Ardışık alt çizgileri tek yap
        while '__' in name:
            name = name.replace('__', '_')
        
        # Başı ve sonundaki alt çizgileri kaldır
        name = name.strip('_')
        
        # Maksimum uzunluk
        if len(name) > 50:
            name = name[:50]
        
        return name or 'Benzer_Dosyalar'


def test_similarity():
    """Test fonksiyonu"""
    analyzer = SimilarityAnalyzer()
    
    # Test örnekleri
    test_pairs = [
        ('document_2023.pdf', 'document_2024.pdf'),
        ('IMG_20230101.jpg', 'IMG_20230102.jpg'),
        ('family_photo.jpg', 'family_photos.jpg'),
        ('report_q1.docx', 'report_q2.docx'),
        ('invoice_123.pdf', 'receipt_456.pdf'),
    ]
    
    print("Benzerlik Analizi Test Sonuçları:")
    print("=" * 60)
    
    for s1, s2 in test_pairs:
        lev = analyzer.levenshtein_similarity(s1, s2)
        jw = analyzer.jaro_winkler_similarity(s1, s2)
        lcs, _ = analyzer.longest_common_substring(s1, s2)
        combined = analyzer.combined_similarity(s1, s2)
        
        print(f"\n{s1} vs {s2}")
        print(f"  Levenshtein: {lev:.3f}")
        print(f"  Jaro-Winkler: {jw:.3f}")
        print(f"  LCS: '{lcs}'")
        print(f"  Combined: {combined:.3f}")
    
    # Gruplama testi
    print("\n\nGruplama Testi:")
    print("=" * 60)
    
    names = [
        'IMG_20230101.jpg',
        'IMG_20230102.jpg',
        'IMG_20230103.jpg',
        'document_2023.pdf',
        'document_2024.pdf',
        'invoice_jan.pdf',
        'invoice_feb.pdf',
        'random_file.txt'
    ]
    
    groups = analyzer.group_by_similarity(names, threshold=0.7)
    
    for group, members in groups.items():
        print(f"\n{group}:")
        for member in members:
            print(f"  - {member}")


if __name__ == '__main__':
    test_similarity()
