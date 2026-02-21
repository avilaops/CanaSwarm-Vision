#!/usr/bin/env python3
"""
CanaSwarm-Vision - Object Detector Mock

Detecta objetos em frames de câmera (pessoas, animais, veículos, obstáculos)
"""

import json
import random
from pathlib import Path
from typing import Dict, List


class ObjectDetector:
    """Detector de objetos usando modelo YOLO-like (simulado)"""
    
    # Classes de objetos detectáveis
    OBJECT_CLASSES = [
        'person', 'tractor', 'truck', 'car', 'animal_cattle', 'animal_horse',
        'animal_dog', 'pole', 'tree', 'rock', 'machinery', 'other_robot'
    ]
    
    # Mapeamento de risco por classe
    RISK_MAPPING = {
        'person': 'high',
        'animal_cattle': 'high',
        'animal_horse': 'high',
        'animal_dog': 'medium',
        'tractor': 'medium',
        'truck': 'medium',
        'car': 'medium',
        'other_robot': 'medium',
        'pole': 'low',
        'tree': 'low',
        'rock': 'low',
        'machinery': 'low'
    }
    
    def __init__(self, model_name: str = "yolo-v8-sugarcane"):
        self.model_name = model_name
        self.inference_count = 0
        self.detections_history = []
    
    def detect_objects(self, frame_data: Dict) -> List[Dict]:
        """
        Detecta objetos em um frame
        
        Em produção, isso seria:
        - Carregar modelo YOLO/EfficientDet
        - Rodar inferência na GPU
        - Aplicar NMS (Non-Maximum Suppression)
        - Retornar bounding boxes e classes
        
        Args:
            frame_data: Dados do frame (posição, condições, etc)
        
        Returns:
            Lista de objetos detectados
        """
        self.inference_count += 1
        
        # Mock: retorna objetos do JSON de exemplo
        if 'detection_results' in frame_data:
            detections = frame_data['detection_results']['objects_detected']
        else:
            # Gera detecções aleatórias se não houver
            detections = self._generate_mock_detections()
        
        self.detections_history.extend(detections)
        return detections
    
    def _generate_mock_detections(self) -> List[Dict]:
        """Gera detecções simuladas"""
        num_objects = random.randint(0, 3)
        detections = []
        
        for i in range(num_objects):
            obj_class = random.choice(self.OBJECT_CLASSES)
            distance = random.uniform(3, 50)
            
            detection = {
                'object_id': f'OBJ-{self.inference_count:03d}-{i:02d}',
                'class': obj_class,
                'confidence': random.uniform(0.6, 0.98),
                'bbox': {
                    'x_min': random.randint(0, 1500),
                    'y_min': random.randint(0, 800),
                    'x_max': random.randint(500, 1920),
                    'y_max': random.randint(200, 1080)
                },
                'distance_m': distance,
                'velocity_m_s': random.uniform(0, 2),
                'risk_level': self._calculate_risk_level(obj_class, distance)
            }
            
            detections.append(detection)
        
        return detections
    
    def _calculate_risk_level(self, obj_class: str, distance_m: float) -> str:
        """Calcula nível de risco baseado em classe e distância"""
        base_risk = self.RISK_MAPPING.get(obj_class, 'low')
        
        # Ajusta risco pela distância
        if distance_m < 5:
            if base_risk == 'low':
                return 'medium'
            elif base_risk == 'medium':
                return 'high'
            else:
                return 'critical'
        elif distance_m < 10:
            if base_risk == 'low':
                return 'low'
            elif base_risk == 'medium':
                return 'medium'
            else:
                return 'high'
        else:
            return base_risk
    
    def calculate_collision_risk(self, detections: List[Dict], robot_velocity: float) -> Dict:
        """
        Calcula risco de colisão baseado em detecções
        
        Args:
            detections: Lista de objetos detectados
            robot_velocity: Velocidade atual do robô (m/s)
        
        Returns:
            Análise de risco de colisão
        """
        high_risk_objects = [d for d in detections if d['risk_level'] in ['high', 'critical']]
        medium_risk_objects = [d for d in detections if d['risk_level'] == 'medium']
        
        # Calcula distância de parada (assumindo desaceleração 2 m/s²)
        stopping_distance_m = (robot_velocity ** 2) / (2 * 2.0) if robot_velocity > 0 else 0
        
        # Objetos dentro da distância de parada
        critical_objects = [
            d for d in detections 
            if d['distance_m'] < stopping_distance_m + 5  # 5m de margem
        ]
        
        # Determina ação requerida
        if critical_objects:
            action = 'emergency_stop'
            warning_level = 'critical'
        elif high_risk_objects:
            closest = min(high_risk_objects, key=lambda x: x['distance_m'])
            if closest['distance_m'] < 15:
                action = 'slow_down'
                warning_level = 'high'
            else:
                action = 'monitor'
                warning_level = 'medium'
        elif medium_risk_objects:
            action = 'monitor'
            warning_level = 'low'
        else:
            action = 'continue'
            warning_level = 'none'
        
        return {
            'total_objects': len(detections),
            'high_risk_count': len(high_risk_objects),
            'medium_risk_count': len(medium_risk_objects),
            'critical_objects': critical_objects,
            'robot_velocity_m_s': robot_velocity,
            'stopping_distance_m': stopping_distance_m,
            'action_required': action,
            'warning_level': warning_level,
            'closest_object_distance_m': min([d['distance_m'] for d in detections]) if detections else float('inf')
        }
    
    def display_detection_summary(self, detections: List[Dict], collision_risk: Dict):
        """Exibe resumo de detecções"""
        print("\n" + "="*70)
        print("👁️  DETECÇÃO DE OBJETOS")
        print("="*70)
        
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   Objetos detectados: {len(detections)}")
        print(f"   Alto risco: {collision_risk['high_risk_count']}")
        print(f"   Médio risco: {collision_risk['medium_risk_count']}")
        
        if detections:
            print(f"\n🎯 OBJETOS DETECTADOS:")
            for i, obj in enumerate(detections, 1):
                risk_icon = "🔴" if obj['risk_level'] in ['high', 'critical'] else "🟡" if obj['risk_level'] == 'medium' else "🟢"
                
                print(f"\n{risk_icon} {i}. {obj['class'].upper().replace('_', ' ')}")
                print(f"   ID: {obj['object_id']}")
                print(f"   Confiança: {obj['confidence']:.2%}")
                print(f"   Distância: {obj['distance_m']:.1f}m")
                print(f"   Velocidade: {obj.get('velocity_m_s', 0):.1f} m/s")
                print(f"   Risco: {obj['risk_level'].upper()}")
        
        print(f"\n⚠️  ANÁLISE DE COLISÃO:")
        print(f"   Nível de alerta: {collision_risk['warning_level'].upper()}")
        print(f"   Ação requerida: {collision_risk['action_required'].upper()}")
        print(f"   Distância de parada: {collision_risk['stopping_distance_m']:.1f}m")
        print(f"   Objeto mais próximo: {collision_risk['closest_object_distance_m']:.1f}m")


if __name__ == "__main__":
    print("👁️  CanaSwarm-Vision - Object Detector Mock\n")
    print("="*70)
    
    # Inicializa detector
    detector = ObjectDetector()
    
    # Carrega frame de exemplo
    frame_file = Path(__file__).parent / "example_camera_feed.json"
    with open(frame_file, 'r', encoding='utf-8') as f:
        frame_data = json.load(f)
    
    print(f"\n📷 Processando frame: {frame_data['frame_id']}")
    print(f"   Câmera: {frame_data['camera_id']}")
    print(f"   Robô: {frame_data['robot_id']}")
    print(f"   Velocidade: {frame_data['robot_position']['velocity_m_s']} m/s")
    
    # Detecta objetos
    detections = detector.detect_objects(frame_data)
    
    # Calcula risco de colisão
    collision_risk = detector.calculate_collision_risk(
        detections,
        frame_data['robot_position']['velocity_m_s']
    )
    
    # Exibe resultados
    detector.display_detection_summary(detections, collision_risk)
    
    print("\n" + "="*70)
    print("✅ DETECÇÃO COMPLETA")
    print("="*70)
    print(f"\n💡 Inferências realizadas: {detector.inference_count}\n")
