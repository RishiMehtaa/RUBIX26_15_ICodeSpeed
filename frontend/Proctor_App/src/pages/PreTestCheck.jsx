// import React, { useState, useEffect } from 'react';
// import { useNavigate, useParams } from 'react-router-dom';
// import { Camera, Mic, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
// import { studentTestsAPI, proctoringAPI } from '../services/api';

// const PreTestCheck = () => {
//   const { testId } = useParams();
//   const navigate = useNavigate();
  
//   // State management for hardware verification
//   const [status, setStatus] = useState('checking'); // 'checking', 'success', 'failed'
//   const [checks, setChecks] = useState({
//     camera: { status: 'pending', label: 'Camera Access' },
//     microphone: { status: 'pending', label: 'Internal Microphone' },
//     audioLevels: { status: 'pending', label: 'Audio Input Detection' }
//   });
//   const [errorMessage, setErrorMessage] = useState('');

//   const builtInKeywords = [
//   'built-in', 
//   'internal', 
//   'onboard', 
//   'integrated', 
//   'array', 
//   'default', 
//   'apple', 
//   'macbook'
// ];

//   const runVerification = async () => {
//     try {
//       setStatus('checking');
//       setErrorMessage('');

//       // 1. Request Media Permissions
//       const stream = await navigator.mediaDevices.getUserMedia({ 
//         video: true, 
//         audio: true 
//       });

//       // 2. Verify Camera
//       setChecks(prev => ({ ...prev, camera: { ...prev.camera, status: 'pass' } }));

//       // 3. Verify Microphone Type (Internal/Built-in)
//       const devices = await navigator.mediaDevices.enumerateDevices();
//       const mics = devices.filter(d => d.kind === 'audioinput');
      
//       const hasBuiltIn = mics.some(m => 
//         builtInKeywords.some(keyword => m.label.toLowerCase().includes(keyword))
//       );

//       if (!hasBuiltIn) {
//         throw new Error("Integrated laptop microphone not detected. Please ensure you are using the system's built-in audio.");
//       }
//       setChecks(prev => ({ ...prev, microphone: { ...prev.microphone, status: 'pass' } }));

//       // 4. Check for Audio Activity (Ensure mic isn't hardware-muted)
//       const audioTrack = stream.getAudioTracks()[0];
//       if (audioTrack.muted || !audioTrack.enabled) {
//         throw new Error("The system microphone is currently disabled or muted at the hardware level.");
//       }
//       setChecks(prev => ({ ...prev, audioLevels: { ...prev.audioLevels, status: 'pass' } }));

//       // Clean up the test stream
//       stream.getTracks().forEach(track => track.stop());
//       setStatus('success');

//     } catch (err) {
//       const errorText = err.message || "Hardware verification failed.";
//       setErrorMessage(errorText);
//       setStatus('failed');
      
//       // Log the failure as a pre-test violation for the admin to see
//       try {
//         await proctoringAPI.reportViolation(testId, {
//           type: 'hardware-precheck-fail',
//           severity: 'high',
//           message: errorText,
//           timestamp: new Date().toISOString()
//         });
//       } catch (logErr) {
//         console.error("Failed to log hardware violation:", logErr);
//       }
//     }
//   };

//   const enterFullScreen = () => {
//   const element = document.documentElement; // Targets the entire browser window
  
//   if (element.requestFullscreen) {
//     element.requestFullscreen();
//   } else if (element.mozRequestFullScreen) { // Firefox
//     element.mozRequestFullScreen();
//   } else if (element.webkitRequestFullscreen) { // Chrome, Safari and Opera
//     element.webkitRequestFullscreen();
//   } else if (element.msRequestFullscreen) { // IE/Edge
//     element.msRequestFullscreen();
//   }
// };

//   useEffect(() => {
//     runVerification();
//   }, [testId]);

//   return (
//     <div className="min-h-screen bg-dark-50 flex items-center justify-center p-4">
//       <div className="card max-w-lg w-full p-8 shadow-xl border-2 border-dark-100">
//         <div className="text-center mb-8">
//           <h1 className="text-2xl font-display font-bold text-dark-900">System Integrity Check</h1>
//           <p className="text-dark-600 mt-2">We are verifying your hardware requirements before starting the exam.</p>
//         </div>

//         <div className="space-y-4 mb-8">
//           {Object.entries(checks).map(([key, check]) => (
//             <div key={key} className="flex items-center justify-between p-4 bg-white border-2 border-dark-100 rounded-xl">
//               <div className="flex items-center gap-3">
//                 {key === 'camera' ? <Camera className="w-5 h-5 text-dark-600" /> : <Mic className="w-5 h-5 text-dark-600" />}
//                 <span className="font-medium text-dark-800">{check.label}</span>
//               </div>
//               {check.status === 'pass' ? (
//                 <CheckCircle2 className="w-6 h-6 text-green-500" />
//               ) : check.status === 'pending' && status === 'checking' ? (
//                 <Loader2 className="w-6 h-6 text-dark-300 animate-spin" />
//               ) : (
//                 <AlertCircle className="w-6 h-6 text-red-500" />
//               )}
//             </div>
//           ))}
//         </div>

//         {status === 'failed' && (
//           <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4 mb-6">
//             <p className="text-red-800 text-sm font-medium flex items-center gap-2">
//               <AlertCircle className="w-4 h-4" />
//               {errorMessage}
//             </p>
//           </div>
//         )}

//         <div className="flex gap-4">
//           {status === 'failed' && (
//             <button onClick={runVerification} className="btn-secondary flex-1 py-3">
//               Retry Check
//             </button>
//           )}
          
//           <button
//             onClick={() => {
//                 navigate(`/student/test/${testId}`)
//                 enterFullScreen();}
//             }
//             disabled={status !== 'success'}
//             className={`flex-1 py-3 font-bold rounded-lg transition-all ${
//               status === 'success' 
//                 ? 'bg-dark-900 text-white hover:bg-black shadow-lg' 
//                 : 'bg-dark-100 text-dark-400 cursor-not-allowed'
//             }`}
//           >
//             {status === 'success' ? 'Proceed to Test' : 'Waiting for Verification...'}
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default PreTestCheck;

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Camera, Mic, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { studentTestsAPI, proctoringAPI } from '../services/api';

const PreTestCheck = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  
  const [status, setStatus] = useState('checking'); 
  const [checks, setChecks] = useState({
    camera: { status: 'pending', label: 'Camera Access' },
    microphone: { status: 'pending', label: 'Internal Microphone' },
    audioLevels: { status: 'pending', label: 'Audio Input Detection' }
  });
  const [errorMessage, setErrorMessage] = useState('');

  const builtInKeywords = [
    'built-in', 'internal', 'onboard', 'integrated', 'array', 'default', 'apple', 'macbook'
  ];

  const runVerification = async () => {
    try {
      setStatus('checking');
      setErrorMessage('');

      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: true 
      });

      setChecks(prev => ({ ...prev, camera: { ...prev.camera, status: 'pass' } }));

      const devices = await navigator.mediaDevices.enumerateDevices();
      const mics = devices.filter(d => d.kind === 'audioinput');
      
      const hasBuiltIn = mics.some(m => 
        builtInKeywords.some(keyword => m.label.toLowerCase().includes(keyword))
      );

      if (!hasBuiltIn) {
        throw new Error("Integrated laptop microphone not detected. Please ensure you are using the system's built-in audio.");
      }
      setChecks(prev => ({ ...prev, microphone: { ...prev.microphone, status: 'pass' } }));

      const audioTrack = stream.getAudioTracks()[0];
      if (audioTrack.muted || !audioTrack.enabled) {
        throw new Error("The system microphone is currently disabled or muted at the hardware level.");
      }
      setChecks(prev => ({ ...prev, audioLevels: { ...prev.audioLevels, status: 'pass' } }));

      stream.getTracks().forEach(track => track.stop());
      setStatus('success');

    } catch (err) {
      const errorText = err.message || "Hardware verification failed.";
      setErrorMessage(errorText);
      setStatus('failed');
      
      try {
        await proctoringAPI.reportViolation(testId, {
          type: 'hardware-precheck-fail',
          severity: 'high',
          message: errorText,
          timestamp: new Date().toISOString()
        });
      } catch (logErr) {
        console.error("Failed to log hardware violation:", logErr);
      }
    }
  };

  const enterFullScreen = () => {
    const element = document.documentElement;
    if (element.requestFullscreen) {
      element.requestFullscreen().catch(err => console.error("Fullscreen error:", err));
    } else if (element.webkitRequestFullscreen) {
      element.webkitRequestFullscreen();
    } else if (element.mozRequestFullScreen) {
      element.mozRequestFullScreen();
    } else if (element.msRequestFullscreen) {
      element.msRequestFullscreen();
    }
  };

  // NEW: Handler with a delay to prevent the dashboard redirect
  const handleProceed = () => {
    // 1. Navigate immediately
    navigate(`/student/tests/${testId}`);

    // 2. Trigger fullscreen after a small delay (150ms)
    // This allows the route change to finish before the browser locks the UI
    setTimeout(() => {
      enterFullScreen();
    }, 150);
  };

  useEffect(() => {
    runVerification();
  }, [testId]);

  return (
    <div className="min-h-screen bg-dark-50 flex items-center justify-center p-4">
      <div className="card max-w-lg w-full p-8 shadow-xl border-2 border-dark-100 bg-white rounded-2xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">System Integrity Check</h1>
          <p className="text-gray-600 mt-2">Verifying hardware before the exam starts.</p>
        </div>

        <div className="space-y-4 mb-8">
          {Object.entries(checks).map(([key, check]) => (
            <div key={key} className="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-xl">
              <div className="flex items-center gap-3">
                {key === 'camera' ? <Camera className="w-5 h-5 text-gray-600" /> : <Mic className="w-5 h-5 text-gray-600" />}
                <span className="font-medium text-gray-800">{check.label}</span>
              </div>
              {check.status === 'pass' ? (
                <CheckCircle2 className="w-6 h-6 text-green-500" />
              ) : check.status === 'pending' && status === 'checking' ? (
                <Loader2 className="w-6 h-6 text-gray-300 animate-spin" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-500" />
              )}
            </div>
          ))}
        </div>

        {status === 'failed' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 text-sm font-medium flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {errorMessage}
            </p>
          </div>
        )}

        <div className="flex gap-4">
          {status === 'failed' && (
            <button onClick={runVerification} className="flex-1 py-3 bg-gray-200 text-gray-800 rounded-lg font-bold">
              Retry Check
            </button>
          )}
          
          <button
            onClick={handleProceed}
            disabled={status !== 'success'}
            className={`flex-1 py-3 font-bold rounded-lg transition-all ${
              status === 'success' 
                ? 'bg-black text-white hover:bg-gray-800 shadow-lg' 
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            {status === 'success' ? 'Proceed to Test' : 'Waiting...'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PreTestCheck;