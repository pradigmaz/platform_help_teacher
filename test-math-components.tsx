import React from 'react';
import { MathComponent } from './frontend/src/components/lectures/MathComponent';
import { MathViewerComponent } from './frontend/src/components/lectures/MathViewerComponent';

// Тестовые формулы для проверки
const testFormulas = [
  // Стрелки и импликации
  { latex: 'A \\to B \\rightarrow C', description: 'Стрелки \\to и \\rightarrow' },
  { latex: 'P \\Rightarrow Q \\Leftarrow R', description: 'Двойные стрелки \\Rightarrow и \\Leftarrow' },
  { latex: 'x \\implies y', description: 'Импликация \\implies' },
  { latex: 'A \\leftrightarrow B \\Leftrightarrow C', description: 'Двусторонние стрелки' },
  
  // Русский текст
  { latex: '\\text{Пусть } x \\in \\mathbb{R}', description: 'Русский текст в \\text{}' },
  { latex: '\\text{Функция } f(x) = x^2 \\text{ непрерывна}', description: 'Смешанный текст и формулы' },
  { latex: '\\forall x \\in \\mathbb{N}: \\text{число } x \\text{ натуральное}', description: 'Кванторы с русским текстом' },
  
  // Комбинации символов
  { latex: '\\lim_{n \\to \\infty} \\sum_{k=1}^n \\frac{1}{k^2} = \\frac{\\pi^2}{6}', description: 'Предел с суммой и стрелкой' },
  { latex: '\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2} \\implies \\text{гауссов интеграл}', description: 'Интеграл с импликацией' },
  { latex: '\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix} \\to \\det = ad - bc', description: 'Матрица со стрелкой' },
  
  // Сложные комбинации
  { latex: 'f: X \\to Y \\Rightarrow \\text{отображение } f \\text{ из } X \\text{ в } Y', description: 'Функция с русским описанием' },
  { latex: '\\text{Если } x \\to \\infty, \\text{ то } \\frac{1}{x} \\to 0', description: 'Пределы с русским текстом' },
];

// Компонент для тестирования
export function MathTestSuite() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Тест математических компонентов</h1>
      <p>Проверка LaTeX формул с настройками: trust: true, strict: false</p>
      
      <div style={{ marginBottom: '40px' }}>
        <h2>MathViewerComponent (только просмотр)</h2>
        {testFormulas.map((formula, index) => (
          <div key={index} style={{ 
            margin: '15px 0', 
            padding: '10px', 
            border: '1px solid #ddd', 
            borderRadius: '5px',
            backgroundColor: '#f9f9f9'
          }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
              {formula.description}
            </div>
            <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#888', marginBottom: '8px' }}>
              {formula.latex}
            </div>
            <div>
              <strong>Display mode:</strong>
              <MathViewerComponent latex={formula.latex} displayMode={true} />
            </div>
            <div style={{ marginTop: '10px' }}>
              <strong>Inline mode:</strong> 
              <MathViewerComponent latex={formula.latex} displayMode={false} />
            </div>
          </div>
        ))}
      </div>

      <div>
        <h2>MathComponent (с редактированием)</h2>
        <p style={{ fontSize: '14px', color: '#666' }}>
          Примечание: MathComponent требует Lexical контекст, поэтому здесь показаны только примеры формул.
          Для полного тестирования используйте компонент внутри LectureEditor.
        </p>
        
        <div style={{ 
          padding: '15px', 
          border: '1px solid #ddd', 
          borderRadius: '5px',
          backgroundColor: '#fff3cd'
        }}>
          <h3>Рекомендуемые формулы для тестирования в редакторе:</h3>
          <ul style={{ fontSize: '14px' }}>
            {testFormulas.slice(0, 5).map((formula, index) => (
              <li key={index} style={{ marginBottom: '5px' }}>
                <code style={{ backgroundColor: '#f8f9fa', padding: '2px 4px', borderRadius: '3px' }}>
                  {formula.latex}
                </code>
                <span style={{ marginLeft: '10px', color: '#666' }}>
                  — {formula.description}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

// Функция для автоматического тестирования
export function testMathRendering() {
  const results = [];
  
  testFormulas.forEach((formula, index) => {
    try {
      // Имитируем рендеринг через KaTeX (как в компонентах)
      const katex = require('katex');
      
      // Тест display mode
      const displayResult = katex.renderToString(formula.latex, {
        displayMode: true,
        throwOnError: false,
        errorColor: '#ef4444',
        trust: true,
        strict: false,
      });
      
      // Тест inline mode
      const inlineResult = katex.renderToString(formula.latex, {
        displayMode: false,
        throwOnError: false,
        errorColor: '#ef4444',
        trust: true,
        strict: false,
      });
      
      const hasDisplayError = displayResult.includes('katex-error');
      const hasInlineError = inlineResult.includes('katex-error');
      
      results.push({
        index: index + 1,
        latex: formula.latex,
        description: formula.description,
        displayMode: !hasDisplayError,
        inlineMode: !hasInlineError,
        success: !hasDisplayError && !hasInlineError
      });
      
    } catch (error) {
      results.push({
        index: index + 1,
        latex: formula.latex,
        description: formula.description,
        displayMode: false,
        inlineMode: false,
        success: false,
        error: error.message
      });
    }
  });
  
  // Выводим результаты
  console.log('\n=== РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ МАТЕМАТИЧЕСКИХ КОМПОНЕНТОВ ===');
  results.forEach(result => {
    const status = result.success ? '✓' : '✗';
    console.log(`${status} Тест ${result.index}: ${result.description}`);
    console.log(`   LaTeX: ${result.latex}`);
    console.log(`   Display: ${result.displayMode ? '✓' : '✗'}, Inline: ${result.inlineMode ? '✓' : '✗'}`);
    if (result.error) {
      console.log(`   Ошибка: ${result.error}`);
    }
    console.log('');
  });
  
  const successCount = results.filter(r => r.success).length;
  console.log(`Успешно: ${successCount}/${results.length}`);
  
  if (successCount === results.length) {
    console.log('🎉 Все формулы работают корректно!');
  } else {
    console.log('⚠️ Некоторые формулы требуют внимания');
  }
  
  return results;
}

export default MathTestSuite;