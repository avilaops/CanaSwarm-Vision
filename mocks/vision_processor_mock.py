#!/usr/bin/env python3
"""
CanaSwarm-Vision - Vision Processor Mock

Processador principal que integra detecção de objetos, lanes e depth
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict


class VisionProcessor:
    """Processador principal de visão computacional"""
    
    def __init__(self, robot_id: str):
        self.robot_id = robot_id
        self.processing_count = 0
        self.processing_history = []
    
    def process_frame(self, frame_data: Dict) -> Dict:
        """
        Processa frame completo de câmera
        
        Etapas:
        1. Detectar objetos (pessoas, animais, obstáculos)
        2. Detectar lanes (linhas de plantio)
        3. Calcular depth map (distância de obstáculos)
        4. Integrar informações
        5. Determinar ações
        
        Args:
            frame_data: Dados do frame (posição, imagem, etc)
        
        Returns:
            Resultado completo de processamento
        """
        start_time = time.time()
        self.processing_count += 1
        
        print(f"\n🎬 Processando frame {frame_data['frame_id']}...")
        
        # 1. Detectar objetos
        print("   📸 Detectando objetos...")
        objects = frame_data.get('detection_results', {}).get('objects_detected', [])
        
        # 2. Detectar lanes
        print("   🛣️  Detectando linhas de plantio...")
        lanes = frame_data.get('lane_detection', {})
        
        # 3. Depth map
        print("   📏 Calculando depth map...")
        depth = frame_data.get('depth_map', {})
        
        # 4. Análise de risco
        print("   ⚠️  Analisando riscos...")
        risk_analysis = self._analyze_risks(objects, lanes, frame_data['robot_position'])
        
        # 5. Determinar ações
        print("   🎯 Determinando ações...")
        actions = self._determine_actions(risk_analysis)
        
        processing_time = (time.time() - start_time) * 1000  # ms
        
        result = {
            'frame_id': frame_data['frame_id'],
            'timestamp': frame_data['timestamp'],
            'robot_id': self.robot_id,
            'processing_time_ms': processing_time,
            'objects': {
                'total': len(objects),
                'high_risk': len([o for o in objects if o['risk_level'] in ['high', 'critical']]),
                'detections': objects
            },
            'lanes': lanes,
            'depth': depth,
            'risk_analysis': risk_analysis,
            'actions': actions
        }
        
        self.processing_history.append(result)
        return result
    
    def _analyze_risks(self, objects: list, lanes: dict, robot_pos: dict) -> Dict:
        """Analisa riscos de colisão e navegação"""
        robot_velocity = robot_pos['velocity_m_s']
        
        # Analisa objetos
        high_risk_objects = [o for o in objects if o['risk_level'] in ['high', 'critical']]
        medium_risk_objects = [o for o in objects if o['risk_level'] == 'medium']
        
        # Distância de parada
        stopping_distance_m = (robot_velocity ** 2) / (2 * 2.0) if robot_velocity > 0 else 0
        
        # Objetos críticos (dentro da distância de parada + margem)
        critical_objects = [
            o for o in objects
            if o['distance_m'] < stopping_distance_m + 5
        ]
        
        # Analisa desvio de lane
        lane_deviation_cm = lanes.get('lane_deviation_cm', 0)
        lane_status = 'ok' if abs(lane_deviation_cm) < 10 else 'deviation'
        
        # Determina nível de risco geral
        if critical_objects:
            overall_risk = 'critical'
        elif high_risk_objects:
            overall_risk = 'high'
        elif medium_risk_objects or lane_status == 'deviation':
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        return {
            'overall_risk_level': overall_risk,
            'collision_risk': {
                'critical_objects': len(critical_objects),
                'high_risk_objects': len(high_risk_objects),
                'stopping_distance_m': stopping_distance_m,
                'closest_object_m': min([o['distance_m'] for o in objects]) if objects else float('inf')
            },
            'navigation_risk': {
                'lane_deviation_cm': lane_deviation_cm,
                'lane_status': lane_status,
                'steering_correction_deg': lanes.get('steering_correction_deg', 0)
            }
        }
    
    def _determine_actions(self, risk_analysis: Dict) -> Dict:
        """Determina ações baseado em análise de risco"""
        overall_risk = risk_analysis['overall_risk_level']
        collision = risk_analysis['collision_risk']
        navigation = risk_analysis['navigation_risk']
        
        actions = {
            'timestamp': datetime.now().isoformat(),
            'priority': 'normal',
            'commands': [],
            'notifications': []
        }
        
        # Ações de segurança
        if overall_risk == 'critical':
            actions['priority'] = 'emergency'
            actions['commands'].append({
                'type': 'emergency_stop',
                'reason': f'{collision["critical_objects"]} objetos críticos detectados',
                'immediate': True
            })
            actions['notifications'].append({
                'target': 'core_coordinator',
                'message': 'Emergency stop - objetos críticos'
            })
            actions['notifications'].append({
                'target': 'operator_dashboard',
                'message': 'Robô parado por segurança'
            })
        
        elif overall_risk == 'high':
            actions['priority'] = 'high'
            closest = collision['closest_object_m']
            if closest < 15:
                actions['commands'].append({
                    'type': 'reduce_velocity',
                    'target_velocity_m_s': 0.5,
                    'reason': f'Objeto a {closest:.1f}m'
                })
        
        elif overall_risk == 'medium':
            actions['priority'] = 'medium'
            actions['commands'].append({
                'type': 'monitor',
                'reason': 'Objetos médio risco ou desvio de lane'
            })
        
        # Correções de navegação
        if abs(navigation['lane_deviation_cm']) > 10:
            actions['commands'].append({
                'type': 'steering_correction',
                'angle_deg': navigation['steering_correction_deg'],
                'reason': f'Desvio de {navigation["lane_deviation_cm"]:.0f}cm'
            })
        
        return actions
    
    def display_processing_result(self, result: Dict):
        """Exibe resultado completo de processamento"""
        print("\n" + "="*70)
        print("👁️  RESULTADO DO PROCESSAMENTO DE VISÃO")
        print("="*70)
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo de processamento: {result['processing_time_ms']:.1f}ms")
        print(f"   FPS efetivo: {1000/result['processing_time_ms']:.1f}")
        
        print(f"\n📊 DETECÇÕES:")
        print(f"   Objetos totais: {result['objects']['total']}")
        print(f"   Alto risco: {result['objects']['high_risk']}")
        
        print(f"\n🛣️  NAVEGAÇÃO:")
        lanes = result['lanes']
        print(f"   Lanes detectadas: {lanes.get('lanes_detected', 0)}")
        print(f"   Desvio lateral: {lanes.get('lane_deviation_cm', 0):.0f} cm")
        print(f"   Status: {lanes.get('lane_deviation_status', 'unknown').upper()}")
        
        print(f"\n⚠️  ANÁLISE DE RISCO:")
        risk = result['risk_analysis']
        risk_icon = "🔴" if risk['overall_risk_level'] in ['critical', 'high'] else "🟡" if risk['overall_risk_level'] == 'medium' else "🟢"
        print(f"   Nível geral: {risk_icon} {risk['overall_risk_level'].upper()}")
        print(f"   Objetos críticos: {risk['collision_risk']['critical_objects']}")
        print(f"   Distância de parada: {risk['collision_risk']['stopping_distance_m']:.1f}m")
        print(f"   Objeto mais próximo: {risk['collision_risk']['closest_object_m']:.1f}m")
        
        print(f"\n🎯 AÇÕES DETERMINADAS:")
        actions = result['actions']
        print(f"   Prioridade: {actions['priority'].upper()}")
        print(f"   Comandos: {len(actions['commands'])}")
        
        for i, cmd in enumerate(actions['commands'], 1):
            print(f"\n   {i}. {cmd['type'].upper()}")
            if 'reason' in cmd:
                print(f"      Motivo: {cmd['reason']}")
            if cmd['type'] == 'reduce_velocity':
                print(f"      Velocidade alvo: {cmd['target_velocity_m_s']} m/s")
            elif cmd['type'] == 'steering_correction':
                print(f"      Correção: {cmd['angle_deg']:.1f}°")


if __name__ == "__main__":
    print("👁️  CanaSwarm-Vision - Vision Processor Mock\n")
    print("="*70)
    
    # Inicializa processador
    processor = VisionProcessor("MICROBOT-001")
    
    # Carrega frame de exemplo
    frame_file = Path(__file__).parent / "example_camera_feed.json"
    with open(frame_file, 'r', encoding='utf-8') as f:
        frame_data = json.load(f)
    
    print(f"\n📷 Frame: {frame_data['frame_id']}")
    print(f"   Robô: {frame_data['robot_id']}")
    print(f"   Posição: ({frame_data['robot_position']['lat']:.4f}, {frame_data['robot_position']['lon']:.4f})")
    print(f"   Velocidade: {frame_data['robot_position']['velocity_m_s']} m/s")
    
    # Processa frame
    result = processor.process_frame(frame_data)
    
    # Exibe resultados
    processor.display_processing_result(result)
    
    # Salva resultado
    output_file = Path(__file__).parent / f"vision_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultado salvo em: {output_file.name}")
    
    print("\n" + "="*70)
    print("✅ PROCESSAMENTO COMPLETO")
    print("="*70)
    print(f"\n💡 Total de frames processados: {processor.processing_count}\n")
