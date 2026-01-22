import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Eye, EyeOff, ShieldCheck, Lock, Mail, User, Upload } from 'lucide-react';

const Signup = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [idImage, setIdImage] = useState(null);
  const [idImagePreview, setIdImagePreview] = useState(null);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please upload a valid image file');
        return;
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('Image size must be less than 5MB');
        return;
      }
      
      setIdImage(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setIdImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const saveIdImageLocally = async (file, userId) => {
    try {
      const storagePath = import.meta.env.VITE_STUDENT_ID_STORAGE_PATH || 'public/uploads/student-ids';
      const timestamp = Date.now();
      const fileName = `${userId}_${timestamp}_${file.name}`;
      const filePath = `${storagePath}/${fileName}`;

      // Convert file to base64 for local storage
      const reader = new FileReader();
      return new Promise((resolve, reject) => {
        reader.onload = () => {
          // Store file info and base64 data
          const imageData = {
            fileName,
            filePath,
            base64: reader.result,
            timestamp
          };
          // Save to localStorage (for demo purposes)
          // In production, you'd send this to backend or use File System API
          const existingImages = JSON.parse(localStorage.getItem('studentIdImages') || '{}');
          existingImages[userId] = imageData;
          localStorage.setItem('studentIdImages', JSON.stringify(existingImages));
          
          resolve(filePath);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    } catch (error) {
      console.error('Error saving ID image:', error);
      throw error;
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // const handleSubmit = async (e) => {
  //   e.preventDefault();
  //   setError('');

  //   if (formData.password !== formData.confirmPassword) {
  //     setError('Passwords do not match');
  //     return;
  //   }

  //   if (formData.password.length < 6) {
  //     setError('Password must be at least 6 characters long');
  //     return;
  //   }

  //   setLoading(true);

  //   try {
  //     const result = await signup(formData.name, formData.email, formData.password, formData.role);
  //     if (result.success) {
  //       if (result.user.role === 'admin') {
  //         navigate('/admin/dashboard');
  //       } else {
  //         navigate('/student/dashboard');
  //       }
  //     } else {
  //       setError(result.error || 'Signup failed');
  //     }
  //   } catch (err) {
  //     setError('An error occurred during signup');
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    if (formData.role === 'student' && !idImage) {
      setError('Please upload your student ID image');
      return;
    }

    setLoading(true);

     try {
      const result = await signup(formData.name, formData.email, formData.password, formData.role);
      if (result.success) {
        // Save ID image locally if signup successful and user is student
        if (formData.role === 'student' && idImage) {
          const imagePath = await saveIdImageLocally(idImage, result.user.id);
          console.log('ID image saved at:', imagePath);
        }

        if (result.user.role === 'admin') {
          navigate('/admin/dashboard');
        } else {
          navigate('/student/dashboard');
        }
      } else {
        setError(result.error || 'Signup failed');
      }
    } catch (err) {
      setError('An error occurred during signup');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen bg-white flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-dark-900 p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <ShieldCheck className="w-10 h-10 text-white" />
            <span className="text-2xl font-display font-bold text-white">AI Proctor</span>
          </div>
          
          <div className="max-w-md">
            <h1 className="text-5xl font-display font-bold text-white mb-6 leading-tight">
              Join the Future of
              <br />
              Online Examinations
            </h1>
            <p className="text-lg text-dark-300 leading-relaxed mb-8">
              Create your account and experience secure, AI-powered proctoring 
              for fair and transparent online assessments.
            </p>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-dark-800 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white font-bold">✓</span>
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-1">Real-time Monitoring</h3>
                  <p className="text-dark-400 text-sm">AI-powered detection of suspicious activities</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-dark-800 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white font-bold">✓</span>
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-1">Detailed Analytics</h3>
                  <p className="text-dark-400 text-sm">Comprehensive reports and audit logs</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-dark-800 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white font-bold">✓</span>
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-1">Easy Setup</h3>
                  <p className="text-dark-400 text-sm">Get started in minutes</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Signup Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <ShieldCheck className="w-8 h-8 text-dark-900" />
            <span className="text-xl font-display font-bold text-dark-900">AI Proctor</span>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-display font-bold text-dark-900 mb-2">
              Create your account
            </h2>
            <p className="text-dark-600">
              Fill in your details to get started
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-dark-700 mb-2">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="input-field pl-12"
                  placeholder="John Doe"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="input-field pl-12"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-700 mb-2">
                Role
              </label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="input-field"
              >
                <option value="student">Student</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            {/* {formData.role === 'student' && (
                <div>
                  <label className="block text-sm font-medium text-dark-700 mb-2">
                    Upload Student ID Image
                  </label>
                  <div className="relative">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setIdImage(e.target.files[0])}
                      className="input-field py-2.5"
                      required
                    />
                    <p className="mt-1 text-xs text-dark-500">
                      Please upload a clear image of your college or government ID for verification.
                    </p>
                  </div>
                </div>
              )} */}

               {formData.role === 'student' && (
              <div>
                <label className="block text-sm font-medium text-dark-700 mb-2">
                  Student ID Image *
                </label>
                <div className="relative">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="hidden"
                    id="id-upload"
                    required
                  />
                  <label
                    htmlFor="id-upload"
                    className="input-field cursor-pointer flex items-center justify-center gap-2 py-3 hover:bg-dark-50 transition-colors"
                  >
                    <Upload className="w-5 h-5 text-dark-400" />
                    <span className="text-dark-600">
                      {idImage ? idImage.name : 'Choose ID image'}
                    </span>
                  </label>
                  {idImagePreview && (
                    <div className="mt-3 border-2 border-dark-200 rounded-lg p-2">
                      <img
                        src={idImagePreview}
                        alt="ID Preview"
                        className="w-full h-48 object-contain rounded"
                      />
                    </div>
                  )}
                  <p className="mt-1 text-xs text-dark-500">
                    Upload a clear image of your college/government ID (Max 5MB)
                  </p>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-dark-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="input-field pl-12 pr-12"
                  placeholder="Create a password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-700 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="input-field pl-12"
                  placeholder="Confirm your password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-dark-600">
              Already have an account?{' '}
              <Link to="/login" className="text-dark-900 font-medium hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;