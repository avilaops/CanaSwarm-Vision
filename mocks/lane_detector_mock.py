#!/usr/bin/env python3
"""
CanaSwarm-Vision - Lane Detector Mock

Detecta linhas de plantio (lanes) para manter robô centralizado
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple


class LaneDetector:
    """Detector de linhas de plantio para navegação assistida"""
    
    def __init__(self):
        self.detection_count = 0
        self.lane_history = []
    
    def detect_lanes(self, frame_data: Dict) -> Dict:
        """
        Detecta linhas de plantio em um frame
        
        Em produção, isso seria:
        - Pré-processamento (grayscale, blur, edge detection)
        - Hough Transform ou CNN-based lane detection
        - Filtragem de linhas paralelas
        - Tracking temporal para suavização
        
        Args:
            frame_data: Dados do frame
        
        Returns:
            Informações de lanes detectadas
        """
        self.detection_count += 1
        
        # Mock: retorna lanes do JSON de exemplo
        if 'lane_detection' in frame_data:
            lane_info = frame_data['lane_detection']
        else:
            # Gera lanes simuladas
            lane_info = self._generate_mock_lanes()
        
        self.lane_history.append(lane_info)
        return lane_info
    
    def _generate_mock_lanes(self) -> Dict:
        """Gera detecção de lanes simulada"""
        lane_info = {
            'lanes_detected': 2,
            'current_lane': 1,
            'lane_lines': [
                {
                    'lane_id': 'LEFT',
                    'points': [
                        {'x': 100, 'y': 1080},
                        {'x': 300, 'y': 800},
                        {'x': 500, 'y': 400},
                        {'x': 600, 'y': 0}
                    ],
                    'confidence': 0.85 + (0.1 * (0.5 - abs(0.5 - (self.detection_count % 10) / 10))),
                    'width_cm': 150
                },
                {
                    'lane_id': 'RIGHT',
                    'points': [
                        {'x': 1300, 'y': 1080},
                        {'x': 1400, 'y': 800},
                        {'x': 1500, 'y': 400},
                        {'x': 1550, 'y': 0}
                    ],
                    'confidence': 0.85 + (0.1 * (0.5 - abs(0.5 - (self.detection_count % 10) / 10))),
                    'width_cm': 150
                }
            ],
            'lane_deviation_cm': -10 + (self.detection_count % 20),
            'lane_deviation_status': 'centered',
            'steering_correction_deg': 0
        }
        
        return lane_info
    
    def calculate_lane_center(self, lane_info: Dict, image_height: int = 1080) -> Tuple[float, float]:
        """
        Calcula centro da lane na parte inferior da imagem
        
        Args:
            lane_info: Informações de lanes
            image_height: Altura da imagem
        
        Returns:
            (x_center, confidence)
        """
        lines = lane_info['lane_lines']
        
        if len(lines) < 2:
            return None, 0.0
        
        # Pega último ponto de cada linha (parte inferior da imagem)
        left_line = next((l for l in lines if l['lane_id'] == 'LEFT'), None)
        right_line = next((l for l in lines if l['lane_id'] == 'RIGHT'), None)
        
        if not left_line or not right_line:
            return None, 0.0
        
        # Ponto mais próximo da base da imagem
        left_bottom = min(left_line['points'], key=lambda p: abs(p['y'] - image_height))
        right_bottom = min(right_line['points'], key=lambda p: abs(p['y'] - image_height))
        
        center_x = (left_bottom['x'] + right_bottom['x']) / 2
        
        # Confiança é mínima das duas linhas
        confidence = min(left_line['confidence'], right_line['confidence'])
        
        return center_x, confidence
    
    def calculate_steering_correction(self, lane_info: Dict, image_width: int = 1920) -> Dict:
        """
        Calcula correção de direção para manter robô centralizado
        
        Args:
            lane_info: Informações de lanes
            image_width: Largura da imagem
        
        Returns:
            Correções de direção
        """
        center_x, confidence = self.calculate_lane_center(lane_info)
        
        if center_x is None:
            return {
                'correction_needed': False,
                'steering_angle_deg': 0,
                'lateral_deviation_px': 0,
                'lateral_deviation_cm': 0,
                'confidence': 0
            }
        
        # Centro da imagem
        image_center = image_width / 2
        
        # Desvio lateral em pixels
        deviation_px = center_x - image_center
        
        # Converte para cm (assumindo 1px = 0.5cm na base da imagem)
        deviation_cm = deviation_px * 0.5
        
        # Calcula ângulo de correção (proporção simples)
        # A cada 10cm de desvio, correção de 1 grau
        steering_angle = deviation_cm / 10.0
        
        # Limita correção a ±15 graus
        steering_angle = max(-15, min(15, steering_angle))
        
        # Determina status
        if abs(deviation_cm) < 5:
            status = 'centered'
        elif deviation_cm > 0:
            status = 'deviation_right'
        else:
            status = 'deviation_left'
        
        return {
            'correction_needed': abs(steering_angle) > 0.5,
            'steering_angle_deg': steering_angle,
            'lateral_deviation_px': deviation_px,
            'lateral_deviation_cm': deviation_cm,
            'deviation_status': status,
            'confidence': confidence
        }
    
    def display_lane_detection(self, lane_info: Dict, steering: Dict):
        """Exibe resumo de detecção de lanes"""
        print("\n" + "="*70)
        print("🛣️  DETECÇÃO DE LINHAS DE PLANTIO")
        print("="*70)
        
        print(f"\n📊 LANES DETECTADAS: {lane_info['lanes_detected']}")
        
        for line in lane_info['lane_lines']:
            conf_icon = "✅" if line['confidence'] > 0.85 else "⚠️"
            print(f"\n{conf_icon} {line['lane_id']}:")
            print(f"   Confiança: {line['confidence']:.2%}")
            print(f"   Largura: {line['width_cm']} cm")
            print(f"   Pontos: {len(line['points'])}")
        
        print(f"\n🎯 POSICIONAMENTO:")
        print(f"   Desvio lateral: {steering['lateral_deviation_cm']:.1f} cm")
        print(f"   Status: {steering['deviation_status'].replace('_', ' ').upper()}")
        
        if steering['correction_needed']:
            direction = "DIREITA" if steering['steering_angle_deg'] > 0 else "ESQUERDA"
            print(f"\n🔄 CORREÇÃO NECESSÁRIA:")
            print(f"   Direção: {direction}")
            print(f"   Ângulo: {abs(steering['steering_angle_deg']):.1f}°")
        else:
            print(f"\n✅ ROBÔ CENTRALIZADO - Nenhuma correção necessária")


if __name__ == "__main__":
    print("🛣️  CanaSwarm-Vision - Lane Detector Mock\n")
    print("="*70)
    
    # Inicializa detector
    detector = LaneDetector()
    
    # Carrega frame de exemplo
    frame_file = Path(__file__).parent / "example_camera_feed.json"
    with open(frame_file, 'r', encoding='utf-8') as f:
        frame_data = json.load(f)
    
    print(f"\n📷 Processando frame: {frame_data['frame_id']}")
    print(f"   Câmera: {frame_data['camera_id']}")
    print(f"   Resolução: {frame_data['camera_specs']['resolution']}")
    
    # Detecta lanes
    lane_info = detector.detect_lanes(frame_data)
    
    # Calcula correção de direção
    steering = detector.calculate_steering_correction(lane_info)
    
    # Exibe resultados
    detector.display_lane_detection(lane_info, steering)
    
    print("\n" + "="*70)
    print("✅ DETECÇÃO DE LANES COMPLETA")
    print("="*70)
    print(f"\n💡 Detecções realizadas: {detector.detection_count}\n")
