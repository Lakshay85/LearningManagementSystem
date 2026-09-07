import { useState, useRef, useCallback } from "react";
import {
  Upload,
  X,
  File,
  CheckCircle,
  AlertCircle,
  Loader2,
  Video,
  Info,
} from "lucide-react";
import facultyApi from "../../utils/facultyApi";
import CustomSelect from "../../components/common/CustomSelect";

// Constants for validation
const ALLOWED_VIDEO_TYPES = [
  "video/mp4",
  "video/webm",
  "video/ogg",
  "video/quicktime",
  "video/x-msvideo",
];

const ALLOWED_EXTENSIONS = [".mp4", ".webm", ".ogg", ".mov", ".avi"];

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB
const MAX_TITLE_LENGTH = 200;
const MAX_DESCRIPTION_LENGTH = 2000;

// Sanitize filename to prevent path traversal and special characters
const sanitizeFilename = (filename) => {
  // Remove path separators and special characters
  return filename
    .replace(/[/\\:*?"<>|]/g, "_")
    .replace(/\.{2,}/g, "_")
    .trim();
};

// Validate file type
const isValidFileType = (file) => {
  const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
  return (
    ALLOWED_VIDEO_TYPES.includes(file.type) ||
    ALLOWED_EXTENSIONS.includes(extension)
  );
};

// Format file size for display
const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// Format duration for display
const formatDuration = (seconds) => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const VideoUpload = () => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [videoDuration, setVideoDuration] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("idle"); // idle, uploading, success, error
  const [errorMessage, setErrorMessage] = useState("");
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    category: "",
    visibility: "private",
  });
  const [validationErrors, setValidationErrors] = useState({});

  const fileInputRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Validate form data
  const validateForm = useCallback(() => {
    const errors = {};

    if (!formData.title.trim()) {
      errors.title = "Title is required";
    } else if (formData.title.length > MAX_TITLE_LENGTH) {
      errors.title = `Title must be less than ${MAX_TITLE_LENGTH} characters`;
    }

    if (formData.description.length > MAX_DESCRIPTION_LENGTH) {
      errors.description = `Description must be less than ${MAX_DESCRIPTION_LENGTH} characters`;
    }

    if (!selectedFile) {
      errors.file = "Please select a video file";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData, selectedFile]);

  // Handle file validation and selection
  const handleFileSelect = useCallback((file) => {
    setErrorMessage("");
    setValidationErrors((prev) => ({ ...prev, file: undefined }));

    // Validate file type
    if (!isValidFileType(file)) {
      setErrorMessage(
        `Invalid file type. Allowed types: ${ALLOWED_EXTENSIONS.join(", ")}`
      );
      return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage(`File size exceeds ${formatFileSize(MAX_FILE_SIZE)} limit`);
      return;
    }

    // Sanitize filename
    const sanitizedName = sanitizeFilename(file.name);
    
    // Create a new file object with sanitized name for display
    setSelectedFile({
      file,
      sanitizedName,
      size: file.size,
      type: file.type,
    });

    // Create video preview and get duration
    const videoUrl = URL.createObjectURL(file);
    setVideoPreview(videoUrl);

    // Get video duration
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      setVideoDuration(video.duration);
      URL.revokeObjectURL(video.src);
    };
    video.src = videoUrl;

    // Auto-fill title if empty
    setFormData((prev) => ({
      ...prev,
      title: prev.title || sanitizedName.replace(/\.[^/.]+$/, ""),
    }));
  }, []);

  // Handle drag events
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        handleFileSelect(files[0]);
      }
    },
    [handleFileSelect]
  );

  // Handle file input change
  const handleFileInputChange = useCallback(
    (e) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFileSelect(files[0]);
      }
    },
    [handleFileSelect]
  );

  // Handle form input changes
  const handleInputChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setValidationErrors((prev) => ({ ...prev, [name]: undefined }));
  }, []);

  // Handle file removal
  const handleRemoveFile = useCallback(() => {
    if (videoPreview) {
      URL.revokeObjectURL(videoPreview);
    }
    setSelectedFile(null);
    setVideoPreview(null);
    setVideoDuration(null);
    setUploadProgress(0);
    setUploadStatus("idle");
    setErrorMessage("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [videoPreview]);

  // Handle upload cancellation
  const handleCancelUpload = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setUploadStatus("idle");
    setUploadProgress(0);
  }, []);

  // Handle upload
  const handleUpload = useCallback(async () => {
    if (!validateForm()) {
      return;
    }

    setUploadStatus("uploading");
    setUploadProgress(0);
    setErrorMessage("");

    abortControllerRef.current = new AbortController();

    try {
      const formDataToSend = new FormData();
      formDataToSend.append("video", selectedFile.file);
      formDataToSend.append("title", formData.title.trim());
      formDataToSend.append("description", formData.description.trim());
      formDataToSend.append("category", formData.category);
      formDataToSend.append("visibility", formData.visibility);

      await facultyApi.uploadVideo(
        formDataToSend,
        (progress) => setUploadProgress(progress),
        abortControllerRef.current.signal
      );

      setUploadStatus("success");
    } catch (error) {
      if (error.message !== "Upload cancelled") {
        setUploadStatus("error");
        setErrorMessage(error.message || "Failed to upload video");
      }
    }
  }, [selectedFile, formData, validateForm]);

  // Reset form
  const handleReset = useCallback(() => {
    handleRemoveFile();
    setFormData({
      title: "",
      description: "",
      category: "",
      visibility: "private",
    });
    setValidationErrors({});
  }, [handleRemoveFile]);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Upload Video</h2>
        <p className="text-gray-500 mt-1">
          Share your educational content with students
        </p>
      </div>

      {/* Upload Status Messages */}
      {uploadStatus === "success" && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <div>
            <p className="font-medium text-green-800">
              Video uploaded successfully!
            </p>
            <p className="text-sm text-green-600">
              Your video is now being processed and will be available shortly.
            </p>
          </div>
          <button
            onClick={handleReset}
            className="ml-auto px-4 py-2 text-sm font-medium text-green-700 hover:text-green-800"
          >
            Upload Another
          </button>
        </div>
      )}

      {uploadStatus === "error" && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <div>
            <p className="font-medium text-red-800">Upload failed</p>
            <p className="text-sm text-red-600">{errorMessage}</p>
          </div>
          <button
            onClick={() => setUploadStatus("idle")}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        {/* Drag and Drop Area */}
        {!selectedFile && (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
              dragActive
                ? "border-emerald-500 bg-emerald-50"
                : "border-gray-300 hover:border-gray-400"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_VIDEO_TYPES.join(",")}
              onChange={handleFileInputChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="flex flex-col items-center">
              <div
                className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${
                  dragActive ? "bg-emerald-100" : "bg-gray-100"
                }`}
              >
                <Upload
                  className={`w-8 h-8 ${
                    dragActive ? "text-emerald-600" : "text-gray-400"
                  }`}
                />
              </div>
              <p className="text-lg font-medium text-gray-700 mb-2">
                Drag and drop your video here
              </p>
              <p className="text-sm text-gray-500 mb-4">
                or click to browse from your computer
              </p>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <Info className="w-4 h-4" />
                <span>
                  Supported formats: MP4, WebM, OGG, MOV, AVI (Max{" "}
                  {formatFileSize(MAX_FILE_SIZE)})
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Selected File Preview */}
        {selectedFile && (
          <div className="space-y-6">
            {/* Video Preview */}
            <div className="relative bg-gray-900 rounded-lg overflow-hidden">
              {videoPreview && (
                <video
                  src={videoPreview}
                  controls
                  className="w-full max-h-80 object-contain"
                >
                  Your browser does not support the video tag.
                </video>
              )}
              {uploadStatus !== "uploading" && (
                <button
                  onClick={handleRemoveFile}
                  className="absolute top-2 right-2 p-2 bg-black/50 hover:bg-black/70 rounded-full text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* File Info */}
            <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
              <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                <Video className="w-6 h-6 text-emerald-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {selectedFile.sanitizedName}
                </p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(selectedFile.size)}
                  {videoDuration && ` • ${formatDuration(videoDuration)}`}
                </p>
              </div>
              {uploadStatus === "uploading" && (
                <button
                  onClick={handleCancelUpload}
                  className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 font-medium"
                >
                  Cancel
                </button>
              )}
            </div>

            {/* Upload Progress */}
            {uploadStatus === "uploading" && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </span>
                  <span className="font-medium text-gray-900">
                    {uploadProgress}%
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Form Fields */}
            {uploadStatus !== "success" && (
              <div className="space-y-4">
                {/* Title */}
                <div>
                  <label
                    htmlFor="title"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    maxLength={MAX_TITLE_LENGTH}
                    disabled={uploadStatus === "uploading"}
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-gray-100 ${
                      validationErrors.title
                        ? "border-red-300"
                        : "border-gray-300"
                    }`}
                    placeholder="Enter video title"
                  />
                  {validationErrors.title && (
                    <p className="mt-1 text-sm text-red-600">
                      {validationErrors.title}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-400">
                    {formData.title.length}/{MAX_TITLE_LENGTH}
                  </p>
                </div>

                {/* Description */}
                <div>
                  <label
                    htmlFor="description"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Description
                  </label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    maxLength={MAX_DESCRIPTION_LENGTH}
                    disabled={uploadStatus === "uploading"}
                    rows={4}
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-gray-100 resize-none ${
                      validationErrors.description
                        ? "border-red-300"
                        : "border-gray-300"
                    }`}
                    placeholder="Describe your video content..."
                  />
                  {validationErrors.description && (
                    <p className="mt-1 text-sm text-red-600">
                      {validationErrors.description}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-400">
                    {formData.description.length}/{MAX_DESCRIPTION_LENGTH}
                  </p>
                </div>

                {/* Category and Visibility */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      htmlFor="category"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Category
                    </label>
                    <CustomSelect
                      id="category"
                      name="category"
                      value={formData.category}
                      onChange={handleInputChange}
                      disabled={uploadStatus === "uploading"}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-gray-100"
                      options={[
                        { value: "", label: "Select category" },
                        { value: "lecture", label: "Lecture" },
                        { value: "tutorial", label: "Tutorial" },
                        { value: "lab", label: "Lab Session" },
                        { value: "seminar", label: "Seminar" },
                        { value: "workshop", label: "Workshop" },
                        { value: "other", label: "Other" },
                      ]}
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="visibility"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Visibility
                    </label>
                    <CustomSelect
                      id="visibility"
                      name="visibility"
                      value={formData.visibility}
                      onChange={handleInputChange}
                      disabled={uploadStatus === "uploading"}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-gray-100"
                      options={[
                        { value: "private", label: "Private" },
                        { value: "public", label: "Public" },
                        { value: "unlisted", label: "Unlisted" },
                      ]}
                    />
                  </div>
                </div>

                {/* Upload Button */}
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    onClick={handleReset}
                    disabled={uploadStatus === "uploading"}
                    className="px-6 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={uploadStatus === "uploading"}
                    className="px-6 py-2.5 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    {uploadStatus === "uploading" ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        Upload Video
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {errorMessage && uploadStatus === "idle" && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">{errorMessage}</span>
          </div>
        )}
      </div>

      {/* Upload Guidelines */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-medium text-blue-800 mb-2">Upload Guidelines</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Videos should be in MP4, WebM, OGG, MOV, or AVI format</li>
          <li>• Maximum file size is 500MB</li>
          <li>• Recommended resolution: 1080p (1920x1080)</li>
          <li>• Ensure you have rights to share the content</li>
          <li>• Videos are scanned for security before processing</li>
        </ul>
      </div>
    </div>
  );
};

export default VideoUpload;
