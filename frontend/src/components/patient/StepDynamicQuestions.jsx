import React, { useEffect, useState } from 'react';
import { HelpCircle, Loader2, ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react';
import { getDynamicQuestions } from '../../services/triageService';

/**
 * Componente Paso 2 del Formulario Híbrido: Preguntas Dinámicas Adaptativas.
 * Consulta la API y renderiza de 2 a 3 preguntas adaptativas para precisar el cuadro clínico.
 */
function StepDynamicQuestions({ formData, updateFormData, onNext, onBack }) {
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState(formData.dynamicAnswers || {});
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchQuestions() {
      setLoading(true);
      setError(null);
      try {
        const response = await getDynamicQuestions(formData.rawSymptoms, formData.age);
        if (isMounted) {
          setQuestions(response.questions || []);
          setLoading(false);
        }
      } catch (err) {
        console.error('Error cargando preguntas dinámicas:', err);
        if (isMounted) {
          // Preguntas por defecto si la API falla
          setQuestions([
            {
              id: 'q_default_1',
              question_text: '¿Sus síntomas han empeorado en las últimas horas?',
              question_type: 'single_choice',
              options: [
                { label: 'Sí, han aumentado notablemente', value: 'si' },
                { label: 'No, se mantienen estables', value: 'no' }
              ]
            }
          ]);
          setLoading(false);
        }
      }
    }

    fetchQuestions();
    return () => { isMounted = false; };
  }, [formData.rawSymptoms, formData.age]);

  const handleSelectOption = (questionId, optionValue, isMultiple = false) => {
    if (isMultiple) {
      const currentList = answers[questionId] || [];
      const updatedList = currentList.includes(optionValue)
        ? currentList.filter((val) => val !== optionValue)
        : [...currentList, optionValue];
      
      const newAnswers = { ...answers, [questionId]: updatedList };
      setAnswers(newAnswers);
      updateFormData({ dynamicAnswers: newAnswers });
    } else {
      const newAnswers = { ...answers, [questionId]: optionValue };
      setAnswers(newAnswers);
      updateFormData({ dynamicAnswers: newAnswers });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onNext();
  };

  if (loading) {
    return (
      <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
        <div className="p-4 bg-sky-500/10 rounded-full border border-sky-500/20">
          <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
        </div>
        <h3 className="text-lg font-semibold text-slate-200">
          Generando Preguntas Adaptativas...
        </h3>
        <p className="text-xs text-slate-400 max-w-sm">
          Analizando el síntoma <span className="text-sky-400 font-medium">"{formData.rawSymptoms}"</span> para precisar banderas rojas médicas.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="border-b border-slate-800 pb-4 mb-4">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-sky-400" /> Paso 2: Preguntas Complementarias
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Responda a continuación para ayudar al profesional médico a evaluar su prioridad.
        </p>
      </div>

      <div className="space-y-6">
        {questions.map((q, idx) => {
          const isMultiple = q.question_type === 'multiple_choice';
          const selectedVal = answers[q.id];

          return (
            <div key={q.id || idx} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-start gap-2">
                <span className="text-xs px-2 py-0.5 bg-sky-500/20 text-sky-400 rounded-md font-mono shrink-0 mt-0.5">
                  Pregunta {idx + 1}
                </span>
                <span>{q.question_text}</span>
              </h3>

              <div className="grid grid-cols-1 gap-2">
                {q.options.map((opt) => {
                  const isSelected = isMultiple
                    ? Array.isArray(selectedVal) && selectedVal.includes(opt.value)
                    : selectedVal === opt.value;

                  return (
                    <button
                      type="button"
                      key={opt.value}
                      onClick={() => handleSelectOption(q.id, opt.value, isMultiple)}
                      className={`w-full text-left p-3 rounded-xl border text-xs font-medium transition duration-150 flex items-center justify-between ${
                        isSelected
                          ? 'bg-sky-500/20 border-sky-500 text-sky-300 shadow-sm'
                          : 'bg-slate-900 border-slate-700/80 text-slate-300 hover:bg-slate-800/80 hover:border-slate-600'
                      }`}
                    >
                      <span>{opt.label}</span>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-sky-400 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onBack}
          className="w-1/3 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-xl transition duration-200 flex items-center justify-center gap-1 text-sm"
        >
          <ArrowLeft className="w-4 h-4" /> Atrás
        </button>

        <button
          type="submit"
          className="w-2/3 py-3.5 px-6 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-sky-500/20 transition duration-200 flex items-center justify-center gap-2"
        >
          <span>Finalizar y Obtener Código QR</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </form>
  );
}

export default StepDynamicQuestions;
