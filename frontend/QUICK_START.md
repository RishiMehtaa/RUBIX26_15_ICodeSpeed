# 🚀 Quick Start Guide - AI Proctor System

## Installation & Setup (5 minutes)

### Step 1: Extract the Project

Extract the `ai-proctor-system` folder to your Desktop.

### Step 2: Install Dependencies

Open terminal/command prompt and run:

```bash
cd Desktop/ai-proctor-system/frontend
npm install
```

This will install all required dependencies (~2-3 minutes).

### Step 3: Start Development Server

```bash
npm run dev
```

The application will open at `http://localhost:3000`

### Step 4: Login & Explore

**Try as Admin:**

- Email: `admin@test.com`
- Password: anything

**Try as Student:**

- Email: `student@test.com`
- Password: anything

## 🎯 What You Can Do Now

### As Admin:

1. ✅ View dashboard with statistics
2. ✅ Create new tests with multiple questions
3. ✅ Manage existing tests (edit, delete, publish)
4. ✅ View all student results with analytics
5. ✅ Export results to CSV

### As Student:

1. ✅ View available tests
2. ✅ Take tests with camera proctoring
3. ✅ See real-time violations and risk score
4. ✅ View results and performance analytics
5. ✅ Track progress over time

## 📋 Key Features to Test

### Proctoring Features:

- **Camera Monitoring**: Allow camera when prompted
- **Tab Switching**: Try switching tabs during test (will be flagged!)
- **Face Detection**: Mock detection runs every 3 seconds
- **Risk Score**: Increases with violations
- **Violation Logs**: All violations are timestamped

### Test Management:

- Create tests with multiple-choice questions
- Set duration and scheduling
- Publish/unpublish tests
- View detailed analytics

## 🎨 Styling & Configuration

### Simple Setup - Just vite.config.js!

This project uses **standard Tailwind CSS** with no custom theme configuration:

- ✅ **Colors**: Standard Tailwind slate colors (slate-50 to slate-900)
- ✅ **Fonts**: Inter font family
- ✅ **Config**: Minimal tailwind.config.js (just content paths)
- ✅ **No Complexity**: Everything uses default Tailwind utilities

**All styling is in the components using standard Tailwind classes!**

### Modify Colors:

The app uses slate colors throughout. To change:

- Edit components and replace `slate-900` with your preferred color
- Or add custom colors in tailwind.config.js if needed

### Change Font:

Edit `src/index.css` and update the Google Fonts import.

## 🔧 Customization

### Change API URL:

Edit `frontend/.env` (create if doesn't exist):

```
VITE_API_URL=http://your-backend-url/api
```

### Add Real AI:

Replace mock proctoring in `frontend/src/pages/TakeTest.jsx` with actual AI model calls.

## 📱 Mobile Testing

The app is fully responsive! Try it on:

- Desktop (best experience)
- Tablet (iPad, etc.)
- Mobile (limited camera proctoring)

## 🐛 Troubleshooting

**Camera not working?**

- Allow camera permissions in browser
- Use HTTPS in production (browsers require it)

**Port 3000 already in use?**

- Edit `vite.config.js` and change the port number

**Dependencies failing?**

- Make sure you have Node.js v16 or higher
- Try `npm cache clean --force` then `npm install`

**Tailwind not working?**

- Make sure all three files exist: vite.config.js, tailwind.config.js, postcss.config.js
- They should all be minimal configs - no customization needed!

## 🎓 Next Steps

1. **Build Backend**: Implement the API endpoints (see README.md)
2. **Add AI Models**: Integrate face detection, pose estimation
3. **Deploy**: Use Vercel (frontend) + your choice for backend
4. **Customize**: Modify UI with standard Tailwind classes

## 📚 Documentation

- Main README: `README.md`
- Frontend README: `frontend/README.md`
- Code is well-commented throughout

## 🎉 You're Ready!

The frontend is 100% complete and works with mock data. It uses **standard Tailwind CSS** - no custom configuration needed! You can:

- Use it as-is for demos
- Integrate with any backend
- Customize with standard Tailwind classes
- Deploy to production

**Enjoy building your AI proctoring system! 🚀**
