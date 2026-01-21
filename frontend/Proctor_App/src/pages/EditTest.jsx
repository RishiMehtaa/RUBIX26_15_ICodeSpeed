import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { testsAPI } from '../services/api';
import { Plus, Trash2, Save, X } from 'lucide-react';

const EditTest = () => {
  const navigate = useNavigate();
  const { testId } = useParams();
  const [testData, setTestData] = useState({
    title: '',
    description: '',
    duration: 60,
    totalMarks: 100,
    startDate: '',
    endDate: '',
  });

  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTestData();
  }, [testId]);

  const fetchTestData = async () => {
    try {
      setLoading(true);
      const response = await testsAPI.getTestById(testId);
      const test = response.data;
      
      // Format test data
      setTestData({
        title: test.title,
        description: test.description,
        duration: test.duration,
        totalMarks: test.total_marks,
        startDate: test.start_date ? new Date(test.start_date).toISOString().slice(0, 16) : '',
        endDate: test.end_date ? new Date(test.end_date).toISOString().slice(0, 16) : '',
      });

      // Format questions
      const formattedQuestions = test.questions.map((q, index) => ({
        id: q.id || `q${index + 1}`,
        question: q.question,
        type: q.type,
        options: q.options || ['', '', '', ''],
        correctAnswer: String(q.correct_answer || '0'),
        marks: q.marks || 1,
      }));

      setQuestions(formattedQuestions);
    } catch (err) {
      console.error('Failed to fetch test:', err);
      setError('Failed to load test data');
    } finally {
      setLoading(false);
    }
  };

  const handleTestDataChange = (e) => {
    const { name, value } = e.target;
    setTestData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleQuestionChange = (questionId, field, value) => {
    setQuestions(questions.map(q =>
      q.id === questionId ? { ...q, [field]: value } : q
    ));
  };

  const handleOptionChange = (questionId, optionIndex, value) => {
    setQuestions(questions.map(q =>
      q.id === questionId
        ? { ...q, options: q.options.map((opt, idx) => idx === optionIndex ? value : opt) }
        : q
    ));
  };

  const addQuestion = () => {
    const newQuestion = {
      id: `q${questions.length + 1}`,
      question: '',
      type: 'multiple-choice',
      options: ['', '', '', ''],
      correctAnswer: '0',
      marks: 1,
    };
    setQuestions([...questions, newQuestion]);
  };

  const removeQuestion = (questionId) => {
    if (questions.length > 1) {
      setQuestions(questions.filter(q => q.id !== questionId));
    }
  };

  const validateForm = () => {
    if (!testData.title.trim()) {
      setError('Test title is required');
      return false;
    }
    if (!testData.description.trim()) {
      setError('Test description is required');
      return false;
    }
    if (testData.duration < 1) {
      setError('Duration must be at least 1 minute');
      return false;
    }
    if (testData.totalMarks < 1) {
      setError('Total marks must be at least 1');
      return false;
    }

    for (let i = 0; i < questions.length; i++) {
      const q = questions[i];
      if (!q.question.trim()) {
        setError(`Question ${i + 1}: Question text is required`);
        return false;
      }
      if (q.type === 'multiple-choice') {
        const hasEmptyOption = q.options.some(opt => !opt.trim());
        if (hasEmptyOption) {
          setError(`Question ${i + 1}: All options must be filled`);
          return false;
        }
      }
    }

    setError(null);
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Format questions for backend
      const formattedQuestions = questions.map(q => ({
        id: q.id,
        question: q.question,
        type: q.type,
        options: q.type === 'multiple-choice' ? q.options : [],
        correct_answer: String(q.correctAnswer),
        marks: q.marks
      }));

      // Format dates
      const startDate = testData.startDate ? new Date(testData.startDate).toISOString() : null;
      const endDate = testData.endDate ? new Date(testData.endDate).toISOString() : null;

      // Prepare payload
      const payload = {
        title: testData.title,
        description: testData.description,
        duration: parseInt(testData.duration),
        total_marks: parseInt(testData.totalMarks),
        questions: formattedQuestions,
        start_date: startDate,
        end_date: endDate
      };

      console.log('Updating test with payload:', payload);

      await testsAPI.updateTest(testId, payload);
      console.log('Test updated successfully');

      setTimeout(() => {
        navigate('/admin/tests');
      }, 1000);
    } catch (err) {
      console.error('Failed to update test:', err);
      console.error('Error details:', err.response?.data);
      setError(err.response?.data?.error || err.response?.data?.details || 'Failed to update test. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-dark-900 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-display font-bold text-dark-900">
            Edit Test
          </h2>
          <p className="text-dark-600 mt-1">
            Update examination details and questions
          </p>
        </div>
        <button
          onClick={() => navigate('/admin/tests')}
          className="btn-secondary flex items-center gap-2"
        >
          <X className="w-4 h-4" />
          Cancel
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="card p-4 border-2 border-red-200 bg-red-50">
          <p className="text-red-800 text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Test Details */}
      <div className="card p-6">
        <h3 className="text-xl font-display font-bold text-dark-900 mb-6">
          Test Details
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-dark-700 mb-2">
              Test Title *
            </label>
            <input
              type="text"
              name="title"
              value={testData.title}
              onChange={handleTestDataChange}
              className="input-field w-full"
              placeholder="e.g., Introduction to Machine Learning"
              required
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-dark-700 mb-2">
              Description *
            </label>
            <textarea
              name="description"
              value={testData.description}
              onChange={handleTestDataChange}
              className="input-field w-full h-24 resize-none"
              placeholder="Brief description of the test..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-700 mb-2">
              Duration (minutes) *
            </label>
            <input
              type="number"
              name="duration"
              value={testData.duration}
              onChange={handleTestDataChange}
              className="input-field w-full"
              min="1"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-700 mb-2">
              Total Marks *
            </label>
            <input
              type="number"
              name="totalMarks"
              value={testData.totalMarks}
              onChange={handleTestDataChange}
              className="input-field w-full"
              min="1"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-700 mb-2">
              Start Date & Time
            </label>
            <input
              type="datetime-local"
              name="startDate"
              value={testData.startDate}
              onChange={handleTestDataChange}
              className="input-field w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-700 mb-2">
              End Date & Time
            </label>
            <input
              type="datetime-local"
              name="endDate"
              value={testData.endDate}
              onChange={handleTestDataChange}
              className="input-field w-full"
            />
          </div>
        </div>
      </div>

      {/* Questions */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-display font-bold text-dark-900">
            Questions ({questions.length})
          </h3>
          <button
            onClick={addQuestion}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Question
          </button>
        </div>

        <div className="space-y-6">
          {questions.map((q, index) => (
            <div key={q.id} className="p-6 bg-dark-50 rounded-xl">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-dark-900">
                  Question {index + 1}
                </h4>
                {questions.length > 1 && (
                  <button
                    onClick={() => removeQuestion(q.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-dark-700 mb-2">
                    Question Text *
                  </label>
                  <textarea
                    value={q.question}
                    onChange={(e) => handleQuestionChange(q.id, 'question', e.target.value)}
                    className="input-field w-full h-20 resize-none"
                    placeholder="Enter your question..."
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-dark-700 mb-2">
                      Question Type
                    </label>
                    <select
                      value={q.type}
                      onChange={(e) => handleQuestionChange(q.id, 'type', e.target.value)}
                      className="input-field w-full"
                    >
                      <option value="multiple-choice">Multiple Choice</option>
                      <option value="text">Text Answer</option>
                      <option value="true-false">True/False</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-dark-700 mb-2">
                      Marks *
                    </label>
                    <input
                      type="number"
                      value={q.marks}
                      onChange={(e) => handleQuestionChange(q.id, 'marks', parseInt(e.target.value) || 1)}
                      className="input-field w-full"
                      min="1"
                      required
                    />
                  </div>
                </div>

                {q.type === 'multiple-choice' && (
                  <div>
                    <label className="block text-sm font-medium text-dark-700 mb-2">
                      Options
                    </label>
                    <div className="space-y-2">
                      {q.options.map((option, optIndex) => (
                        <div key={optIndex} className="flex items-center gap-2">
                          <input
                            type="radio"
                            name={`correct-${q.id}`}
                            checked={q.correctAnswer === String(optIndex)}
                            onChange={() => handleQuestionChange(q.id, 'correctAnswer', String(optIndex))}
                            className="w-4 h-4"
                          />
                          <input
                            type="text"
                            value={option}
                            onChange={(e) => handleOptionChange(q.id, optIndex, e.target.value)}
                            className="input-field flex-1"
                            placeholder={`Option ${optIndex + 1}`}
                          />
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-dark-500 mt-2">
                      Select the radio button for the correct answer
                    </p>
                  </div>
                )}

                {q.type === 'text' && (
                  <div>
                    <label className="block text-sm font-medium text-dark-700 mb-2">
                      Expected Answer (for reference)
                    </label>
                    <textarea
                      value={q.correctAnswer}
                      onChange={(e) => handleQuestionChange(q.id, 'correctAnswer', e.target.value)}
                      className="input-field w-full h-20 resize-none"
                      placeholder="Enter expected answer keywords or criteria..."
                    />
                    <p className="text-xs text-dark-500 mt-1">
                      This will not be auto-graded. Manual grading required.
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4 justify-end sticky bottom-6">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving Changes...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
};

export default EditTest;