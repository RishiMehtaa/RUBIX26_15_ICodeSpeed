import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { testsAPI } from '../services/api';
import { 
  ArrowLeft, 
  Clock, 
  FileText, 
  Calendar,
  Edit,
  Trash2,
  Send,
  CheckCircle2
} from 'lucide-react';

const ViewTest = () => {
  const navigate = useNavigate();
  const { testId } = useParams();
  const [test, setTest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTestDetails();
  }, [testId]);

  const fetchTestDetails = async () => {
    try {
      setLoading(true);
      const response = await testsAPI.getTestById(testId);
      setTest(response.data);
    } catch (err) {
      console.error('Failed to fetch test details:', err);
      setError('Failed to load test details');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this test? This action cannot be undone.')) {
      try {
        await testsAPI.deleteTest(testId);
        navigate('/admin/tests');
      } catch (err) {
        console.error('Failed to delete test:', err);
        alert('Failed to delete test: ' + (err.response?.data?.error || 'Please try again'));
      }
    }
  };

  const handlePublish = async () => {
    try {
      await testsAPI.publishTest(testId);
      setTest({ ...test, visibility: 'published' });
    } catch (err) {
      console.error('Failed to publish test:', err);
      alert('Failed to publish test: ' + (err.response?.data?.error || 'Please try again'));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-dark-900 border-t-transparent"></div>
      </div>
    );
  }

  if (error || !test) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Test not found'}</p>
          <button onClick={() => navigate('/admin/tests')} className="btn-primary">
            Back to Tests
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/admin/tests')}
          className="btn-secondary flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Tests
        </button>
        <div className="flex gap-2">
          <Link
            to={`/admin/tests/${testId}/edit`}
            className="btn-secondary flex items-center gap-2"
          >
            <Edit className="w-4 h-4" />
            Edit
          </Link>
          {test.visibility === 'draft' && (
            <button
              onClick={handlePublish}
              className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium 
                       hover:bg-green-700 transition-all flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Publish
            </button>
          )}
          <button
            onClick={handleDelete}
            className="px-4 py-2 bg-red-50 text-red-600 rounded-lg font-medium 
                     hover:bg-red-100 transition-all flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>

      {/* Test Details Card */}
      <div className="card p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-display font-bold text-dark-900 mb-2">
              {test.title}
            </h2>
            <span
              className={`
                badge
                ${test.visibility === 'published' ? 'badge-success' : 'badge-warning'}
              `}
            >
              {test.visibility}
            </span>
          </div>
        </div>

        <p className="text-dark-600 mb-6">{test.description}</p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-dark-50 rounded-lg">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-dark-600" />
            <div>
              <p className="text-xs text-dark-500">Duration</p>
              <p className="font-semibold text-dark-900">{test.duration} min</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-dark-600" />
            <div>
              <p className="text-xs text-dark-500">Questions</p>
              <p className="font-semibold text-dark-900">{test.total_questions}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-dark-600" />
            <div>
              <p className="text-xs text-dark-500">Total Marks</p>
              <p className="font-semibold text-dark-900">{test.total_marks}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-dark-600" />
            <div>
              <p className="text-xs text-dark-500">Created</p>
              <p className="font-semibold text-dark-900">
                {new Date(test.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {(test.start_date || test.end_date) && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-dark-900 mb-2">Test Schedule</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {test.start_date && (
                <div>
                  <p className="text-dark-600">Start Date</p>
                  <p className="font-medium text-dark-900">
                    {new Date(test.start_date).toLocaleString()}
                  </p>
                </div>
              )}
              {test.end_date && (
                <div>
                  <p className="text-dark-600">End Date</p>
                  <p className="font-medium text-dark-900">
                    {new Date(test.end_date).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Questions */}
      <div className="card p-6">
        <h3 className="text-xl font-display font-bold text-dark-900 mb-6">
          Questions ({test.questions.length})
        </h3>

        <div className="space-y-6">
          {test.questions.map((question, index) => (
            <div key={question.id || index} className="p-6 bg-dark-50 rounded-xl">
              <div className="flex items-start justify-between mb-4">
                <h4 className="font-semibold text-dark-900">
                  Question {index + 1}
                </h4>
                <div className="flex items-center gap-4 text-sm">
                  <span className="badge badge-primary">
                    {question.type}
                  </span>
                  <span className="text-dark-600">
                    {question.marks} {question.marks === 1 ? 'mark' : 'marks'}
                  </span>
                </div>
              </div>

              <p className="text-dark-900 mb-4 whitespace-pre-wrap">
                {question.question}
              </p>

              {question.type === 'multiple-choice' && question.options && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-dark-700 mb-2">Options:</p>
                  {question.options.map((option, optIndex) => (
                    <div
                      key={optIndex}
                      className={`
                        p-3 rounded-lg flex items-center gap-2
                        ${String(question.correct_answer) === String(optIndex)
                          ? 'bg-green-50 border-2 border-green-500'
                          : 'bg-white border border-dark-200'
                        }
                      `}
                    >
                      <div
                        className={`
                          w-6 h-6 rounded-full flex items-center justify-center text-sm
                          ${String(question.correct_answer) === String(optIndex)
                            ? 'bg-green-500 text-white'
                            : 'bg-dark-100 text-dark-600'
                          }
                        `}
                      >
                        {String.fromCharCode(65 + optIndex)}
                      </div>
                      <span className="text-dark-900">{option}</span>
                      {String(question.correct_answer) === String(optIndex) && (
                        <CheckCircle2 className="w-5 h-5 text-green-600 ml-auto" />
                      )}
                    </div>
                  ))}
                </div>
              )}

              {question.type === 'text' && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-dark-700 mb-1">
                    Expected Answer (for reference):
                  </p>
                  <p className="text-dark-900 whitespace-pre-wrap">
                    {question.correct_answer || 'No reference answer provided'}
                  </p>
                  <p className="text-xs text-dark-500 mt-2">
                    * This requires manual grading
                  </p>
                </div>
              )}

              {question.type === 'true-false' && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-sm font-medium text-dark-700 mb-1">
                    Correct Answer:
                  </p>
                  <p className="text-dark-900 font-semibold">
                    {question.correct_answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ViewTest;