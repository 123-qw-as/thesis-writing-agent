import sys
sys.path.insert(0, '.')

print('Testing AIGC detector...')
from src.tools.aigc_detector import detect_aigc

test_text = '''deep learning is a branch of machine learning. first, deep learning uses multi-layer neural networks for feature extraction. second, deep learning has achieved significant results in image classification and object detection. finally, methods like ResNet and Transformer are widely used.'''

result = detect_aigc(test_text)
print(f'AIGC Score: {result["aigc_score"]}%')
print(f'Risk Level: {result["risk_level"]}')
print(f'Patterns found: {result["pattern_count"]}')

print('\nTesting Data verifier...')
from src.tools.data_verifier import verify_data

test_data_text = '''our method achieves 95.5% accuracy on ImageNet. on COCO dataset, mAP is 42.3%. compared to baseline, we improve by 3.2 percentage points. training time is about 10 hours using 4 NVIDIA RTX 3090 GPUs.'''

data_result = verify_data(test_data_text)
print(f'Authenticity Score: {data_result["authenticity_score"]}%')
print(f'Suspicious points: {len(data_result["suspicious_data_points"])}')
print(f'Inconsistencies: {len(data_result["numerical_inconsistencies"])}')

print('\nTesting Evaluation Agent...')
from src.agents.evaluation.agent import evaluate_thesis

thesis_sample = '''# Image Classification Research

## Abstract
This paper proposes a novel deep learning method for image classification. Our method achieves 95.5% accuracy on ImageNet, significantly outperforming baseline methods.

## Introduction
Image classification is a fundamental task in computer vision. With the development of deep learning, CNNs have become the dominant approach.

## Method
We propose an improved CNN architecture with attention mechanisms. Our model uses residual connections and depth-wise separable convolutions.

## Experiment
We conduct experiments on ImageNet and COCO datasets. Results show our method achieves 95.5% accuracy, improving 3.2% over baseline.

## Conclusion
This paper presents an effective image classification method with attention mechanisms.'''

import asyncio
async def test_eval():
    report = await evaluate_thesis(thesis_sample, 'Image Classification Research', iteration=1)
    print(f'Overall Score: {report.overall_score}/10')
    print(f'AIGC Score: {report.aigc_score}%')
    print(f'Data Authenticity: {report.data_authenticity}%')
    print(f'Is Pass: {report.is_pass}')
    return report

report = asyncio.run(test_eval())

print('\nAll tests passed!')