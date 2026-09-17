import { useState, useEffect, useRef } from "react";
import {
  ArrowLeft,
  Video,
  FileText,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Play,
  Pause,
  Download,
  CheckCircle,
  Clock,
  File,
  FileSpreadsheet,
  Presentation,
  Loader2,
  Volume2,
  VolumeX,
  Maximize,
  SkipBack,
  SkipForward,
  MessageSquare,
  X,
  ClipboardCheck,
} from "lucide-react";
import studentApi from "../../utils/studentApi";
import ChatInterface from "../components/ChatInterface";
import Quiz from "./Quiz";
import CourseQuizList from "./CourseQuizList";

const ContentTypeIcon = ({ type, className = "w-5 h-5" }) => {
  switch (type) {
    case "video":
      return <Video className={`${className} text-blue-500`} />;
    case "document":
      return <FileText className={`${className} text-green-500`} />;
    case "text":
      return <BookOpen className={`${className} text-purple-500`} />;
    case "quiz":
      return <ClipboardCheck className={`${className} text-amber-500`} />;
    default:
      return <File className={`${className} text-gray-500`} />;
  }
};

const DocumentViewer = ({ document, content }) => {
  const [loading, setLoading] = useState(true);
  const [viewerFailed, setViewerFailed] = useState(false);
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const getDocumentUrl = () => {
    if (document?.id) {
      // Use document ID with the preview endpoint
      return `${baseUrl}/courses/documents/${document.id}/preview`;
    }
    return null;
  };

  const isPdf = document?.mimeType?.includes("pdf");

  // Check if it's an Office document (Word, Excel, PowerPoint)
  const isOfficeDoc =
    document?.mimeType &&
    (document.mimeType.includes("word") ||
      document.mimeType.includes("document") ||
      document.mimeType.includes("spreadsheet") ||
      document.mimeType.includes("excel") ||
      document.mimeType.includes("presentation") ||
      document.mimeType.includes("powerpoint") ||
      document.mimeType.includes("msword") ||
      document.mimeType.includes("officedocument"));

  // Get Office Online Viewer URL
  const getOfficeViewerUrl = () => {
    const docUrl = getDocumentUrl();
    if (!docUrl) return null;
    // Microsoft Office Online Viewer - works when URL is publicly accessible
    return `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(
      docUrl
    )}`;
  };

  // Get the viewer URL for PDFs
  const getPdfViewerUrl = () => {
    const docUrl = getDocumentUrl();
    if (!docUrl) return null;
    return `${docUrl}#toolbar=0&navpanes=0`;
  };

  // Get document type label
  const getDocumentTypeLabel = () => {
    if (
      document?.mimeType?.includes("word") ||
      document?.mimeType?.includes("msword")
    ) {
      return "Microsoft Word Document";
    } else if (
      document?.mimeType?.includes("excel") ||
      document?.mimeType?.includes("spreadsheet")
    ) {
      return "Microsoft Excel Spreadsheet";
    } else if (
      document?.mimeType?.includes("powerpoint") ||
      document?.mimeType?.includes("presentation")
    ) {
      return "Microsoft PowerPoint Presentation";
    }
    return "Office Document";
  };

  // Timeout fallback for Office docs - if viewer doesn't load in 8 seconds, show fallback
  useEffect(() => {
    if (isOfficeDoc && loading && !viewerFailed) {
      const timeout = setTimeout(() => {
        setLoading(false);
        setViewerFailed(true);
      }, 8000);
      return () => clearTimeout(timeout);
    }
  }, [isOfficeDoc, loading, viewerFailed]);

  // Fallback card for when viewer fails
  const renderFallbackCard = () => (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md">
        <File className="w-16 h-16 text-blue-500 mx-auto mb-4" />
        <h4 className="text-lg font-medium text-gray-900 mb-2">
          {document?.originalFilename}
        </h4>
        <p className="text-gray-500 mb-4">{getDocumentTypeLabel()}</p>
        <div className="text-sm text-gray-400 mb-4">
          {document?.fileSize
            ? `${(document.fileSize / 1024).toFixed(1)} KB`
            : ""}
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="text-sm text-amber-700">
            📄 This document will be viewable after deployment. For now, please
            contact your instructor if you need access.
          </p>
        </div>
        <span className="inline-block mt-4 px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
          Preview Only - No Editing
        </span>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-green-500" />
          <div>
            <h3 className="font-semibold text-gray-900">{content.title}</h3>
            <p className="text-sm text-gray-500">
              {document?.originalFilename}
            </p>
          </div>
        </div>
        <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
          Preview Only
        </span>
      </div>

      <div className="flex-1 bg-gray-100 p-4 overflow-auto">
        {isPdf && getPdfViewerUrl() ? (
          <div className="h-full">
            {loading && (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              </div>
            )}
            <iframe
              src={getPdfViewerUrl()}
              className="w-full h-full rounded-lg shadow-lg bg-white"
              onLoad={() => setLoading(false)}
              style={{
                display: loading ? "none" : "block",
                minHeight: "600px",
              }}
              title={content.title}
            />
          </div>
        ) : isOfficeDoc && getDocumentUrl() ? (
          viewerFailed ? (
            renderFallbackCard()
          ) : (
            <div className="h-full">
              {loading && (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                  <p className="ml-3 text-gray-500">
                    Loading document viewer...
                  </p>
                </div>
              )}
              <iframe
                src={getOfficeViewerUrl()}
                className="w-full h-full rounded-lg shadow-lg bg-white"
                onLoad={() => setLoading(false)}
                onError={() => {
                  setLoading(false);
                  setViewerFailed(true);
                }}
                style={{
                  display: loading ? "none" : "block",
                  minHeight: "600px",
                }}
                title={content.title}
              />
            </div>
          )
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <File className="w-16 h-16 text-gray-400 mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              Document Preview
            </h4>
            <p className="text-gray-500 mb-2">
              This document type cannot be previewed in the browser.
            </p>
            <p className="text-sm text-gray-400">
              Preview only - editing is not allowed
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

const VideoPlayer = ({ video, content }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:3000";

  // Fetch video with credentials and create blob URL
  useEffect(() => {
    if (!video?.id) return;

    const fetchVideo = async () => {
      try {
        setLoading(true);
        setError(null);

        // Import axios with credentials
        const axios = (await import("axios")).default;

        const response = await axios.get(
          `${baseUrl}/videos/stream/${video.id}`,
          {
            responseType: "blob",
            withCredentials: true,
            headers: {
              Accept: "video/*",
            },
          }
        );

        // Create object URL from blob
        const url = URL.createObjectURL(response.data);
        setVideoUrl(url);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching video:", err);
        setError("Failed to load video. Please check your access permissions.");
        setLoading(false);
      }
    };

    fetchVideo();

    // Cleanup: revoke object URL when component unmounts or video changes
    return () => {
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
    };
  }, [video?.id, baseUrl]);

  const getVideoUrl = () => {
    return videoUrl;
  };

  // Handle missing video data
  if (!video || !video.id) {
    return (
      <div className="h-full flex flex-col bg-black">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
              <Video className="w-8 h-8 text-red-500" />
            </div>
            <h4 className="text-white font-semibold mb-2">
              Video Not Available
            </h4>
            <p className="text-gray-300 text-sm">
              This video could not be loaded. Please try selecting another
              lesson.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
      setLoading(false);
      setError(null);
    }
  };

  const handleVideoError = () => {
    setLoading(false);
    setError(
      "Failed to load video. Please check your connection or try again later."
    );
  };

  const handleSeek = (e) => {
    const seekTime = (e.target.value / 100) * duration;
    if (videoRef.current) {
      videoRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
    }
  };

  const skip = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime += seconds;
    }
  };

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoRef.current.requestFullscreen();
      }
    }
  };

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <div className="h-full flex flex-col bg-black">
      {/* Video Container */}
      <div className="flex-1 relative flex items-center justify-center">
        {error ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                <Video className="w-8 h-8 text-red-500" />
              </div>
              <h4 className="text-white font-semibold mb-2">
                Unable to Play Video
              </h4>
              <p className="text-gray-300 text-sm mb-4">{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  setLoading(true);
                  if (videoRef.current) {
                    videoRef.current.load();
                  }
                }}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        ) : loading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin text-white mx-auto mb-4" />
              <p className="text-gray-300 text-sm">Loading video...</p>
            </div>
          </div>
        ) : null}
        <video
          ref={videoRef}
          src={getVideoUrl()}
          className="max-w-full max-h-full"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
          onError={handleVideoError}
          onLoadStart={() => setLoading(true)}
        />
      </div>

      {/* Video Controls */}
      <div className="bg-gray-900 p-4 space-y-3">
        {/* Progress Bar */}
        <div className="flex items-center gap-3">
          <span className="text-white text-sm w-14">
            {formatTime(currentTime)}
          </span>
          <input
            type="range"
            min="0"
            max="100"
            value={duration ? (currentTime / duration) * 100 : 0}
            onChange={handleSeek}
            className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <span className="text-white text-sm w-14">
            {formatTime(duration)}
          </span>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => skip(-10)}
              className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <SkipBack className="w-5 h-5" />
            </button>
            <button
              onClick={togglePlay}
              className="p-3 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-colors"
            >
              {isPlaying ? (
                <Pause className="w-6 h-6" />
              ) : (
                <Play className="w-6 h-6" />
              )}
            </button>
            <button
              onClick={() => skip(10)}
              className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <SkipForward className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center gap-3">
            {/* Volume */}
            <div className="flex items-center gap-2">
              <button
                onClick={toggleMute}
                className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
              >
                {isMuted ? (
                  <VolumeX className="w-5 h-5" />
                ) : (
                  <Volume2 className="w-5 h-5" />
                )}
              </button>
              <input
                type="range"
                min="0"
                max="100"
                value={isMuted ? 0 : volume * 100}
                onChange={(e) => {
                  const newVolume = e.target.value / 100;
                  setVolume(newVolume);
                  if (videoRef.current) {
                    videoRef.current.volume = newVolume;
                  }
                  if (newVolume > 0) setIsMuted(false);
                }}
                className="w-20 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <Maximize className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Video Info */}
        <div className="text-white">
          <h3 className="font-semibold">{content.title}</h3>
          {content.description && (
            <p className="text-sm text-gray-400 mt-1">{content.description}</p>
          )}
        </div>
      </div>
    </div>
  );
};

const TextContent = ({ content }) => {
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-3 p-4 border-b border-gray-200 bg-white">
        <BookOpen className="w-6 h-6 text-purple-500" />
        <h3 className="font-semibold text-gray-900">{content.title}</h3>
      </div>
      <div className="flex-1 p-6 overflow-auto bg-white">
        <div className="prose max-w-none">
          {content.textContent || (
            <p className="text-gray-500">No text content available.</p>
          )}
        </div>
      </div>
    </div>
  );
};

const SidebarSection = ({ section, selectedContent, onSelectContent }) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="border-b border-gray-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center font-semibold text-sm">
            {section.order}
          </span>
          <span className="font-medium text-gray-900 text-left">
            {section.title}
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="pb-2">
          {section.contents.map((content) => (
            <button
              key={content.id}
              onClick={() => onSelectContent(content, section)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${selectedContent?.id === content.id
                ? "bg-indigo-50 border-l-4 border-indigo-600"
                : "hover:bg-gray-50 border-l-4 border-transparent"
                }`}
            >
              <ContentTypeIcon type={content.contentType} className="w-4 h-4" />
              <span
                className={`text-sm flex-1 ${selectedContent?.id === content.id
                  ? "text-indigo-600 font-medium"
                  : "text-gray-600"
                  }`}
              >
                {content.title}
              </span>
              {content.estimatedMinutes && (
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {content.estimatedMinutes}m
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const CourseViewer = ({ course: initialCourse, onBack }) => {
  const [courseData, setCourseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedContent, setSelectedContent] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [showQuizzesView, setShowQuizzesView] = useState(false);

  useEffect(() => {
    const fetchCourseContent = async () => {
      try {
        setLoading(true);
        // Reset selected content when course changes
        setSelectedContent(null);
        setShowQuizzesView(false);
        const data = await studentApi.getEnrolledCourseContent(
          initialCourse.courseId || initialCourse.id
        );
        setCourseData(data);
        // Don't auto-select any content - let student choose what to view
      } catch (err) {
        console.error("Failed to fetch course content:", err);
        setError("Failed to load course content. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchCourseContent();
  }, [initialCourse]);

  const handleSelectContent = (content) => {
    setSelectedContent(content);
    setShowQuizzesView(false);
  };

  const renderContentViewer = () => {
    if (!selectedContent) {
      return (
        <div className="h-full flex items-center justify-center bg-gray-100">
          <div className="text-center">
            <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Select a lesson to start learning</p>
          </div>
        </div>
      );
    }

    switch (selectedContent.contentType) {
      case "video":
        return (
          <VideoPlayer
            video={selectedContent.video}
            content={selectedContent}
          />
        );
      case "document":
        return (
          <DocumentViewer
            document={selectedContent.document}
            content={selectedContent}
          />
        );
      case "text":
        return <TextContent content={selectedContent} />;
      case "quiz":
        return (
          <div className="h-full overflow-y-auto p-4 bg-gray-50">
            <Quiz
              quizId={selectedContent.quizId}
            />
          </div>
        );
      default:
        return (
          <div className="h-full flex items-center justify-center bg-gray-100">
            <p className="text-gray-500">Unknown content type</p>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-indigo-500 mx-auto mb-4" />
          <p className="text-gray-500">Loading course content...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-red-500" />
          </div>
          <p className="text-gray-900 font-medium mb-2">Error Loading Course</p>
          <p className="text-gray-500 mb-4">{error}</p>
          <button
            onClick={onBack}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-4 p-4 border-b border-gray-200 bg-white flex-shrink-0">
        <button
          onClick={onBack}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="font-bold text-gray-900 truncate">
            {courseData?.title}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setShowQuizzesView(!showQuizzesView);
              if (!showQuizzesView) setSelectedContent(null);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              showQuizzesView
                ? 'bg-amber-500 text-white shadow-sm'
                : 'text-amber-700 bg-amber-50 hover:bg-amber-100'
            }`}
          >
            <ClipboardCheck className="w-4 h-4" />
            <span>Course Quizzes</span>
          </button>
          <button
            onClick={() => setShowChat(!showChat)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all transform hover:scale-105 ${showChat
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
              : 'text-indigo-600 bg-indigo-50 hover:bg-indigo-100'
              }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span className="font-medium">Ask AI</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Content Viewer */}
        <div className="flex-1 overflow-hidden">
          {showQuizzesView ? (
            <div className="h-full overflow-y-auto p-4 bg-gray-50">
              <CourseQuizList
                courseId={courseData?.id || initialCourse?.courseId || initialCourse?.id}
                courseTitle={courseData?.title}
              />
            </div>
          ) : (
            renderContentViewer()
          )}
        </div>

        {/* Course Sidebar */}
        <div className="w-80 bg-white overflow-y-auto flex-shrink-0">
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Course Content</h3>
            <p className="text-sm text-gray-500 mt-1">
              {courseData?.sections?.length || 0} sections •{" "}
              {courseData?.sections?.reduce(
                (acc, s) => acc + (s.contents?.length || 0),
                0
              ) || 0}{" "}
              lessons
            </p>
          </div>
          <div>
            {courseData?.sections?.map((section) => (
              <SidebarSection
                key={section.id}
                section={section}
                selectedContent={selectedContent}
                onSelectContent={handleSelectContent}
              />
            ))}
          </div>
        </div>

        {/* AI Chat Panel */}
        {showChat && (
          <div className="w-96 border-l border-gray-200 flex-shrink-0 animate-in slide-in-from-right duration-300">
            <ChatInterface
              courseId={courseData?.id || initialCourse?.courseId || initialCourse?.id}
              courseName={courseData?.title}
              isOpen={showChat}
              onClose={() => setShowChat(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseViewer;
