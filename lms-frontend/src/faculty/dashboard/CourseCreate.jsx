import { useState, useRef, useCallback, useEffect } from "react";
import {
  Upload,
  X,
  File,
  CheckCircle,
  AlertCircle,
  Loader2,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  BookOpen,
  FileText,
  Video,
  GripVertical,
  ArrowLeft,
} from "lucide-react";
import facultyApi from "../../utils/facultyApi";

// Constants for validation
const ALLOWED_DOCUMENT_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.ms-powerpoint",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "text/plain",
];

const ALLOWED_VIDEO_TYPES = [
  "video/mp4",
  "video/webm",
  "video/ogg",
  "video/quicktime",
];

const ALLOWED_DOCUMENT_EXTENSIONS = [
  ".pdf",
  ".doc",
  ".docx",
  ".ppt",
  ".pptx",
  ".xls",
  ".xlsx",
  ".txt",
];

const MAX_DOCUMENT_SIZE = 5 * 1024 * 1024; // 5MB
const MAX_VIDEO_SIZE = 500 * 1024 * 1024; // 500MB
const MAX_TITLE_LENGTH = 200;
const MAX_DESCRIPTION_LENGTH = 2000;

// Course categories
const COURSE_CATEGORIES = [
  { value: "", label: "Select a category" },
  { value: "programming", label: "Programming" },
  { value: "web_development", label: "Web Development" },
  { value: "mobile_development", label: "Mobile Development" },
  { value: "data_science", label: "Data Science" },
  { value: "machine_learning", label: "Machine Learning" },
  { value: "cloud_computing", label: "Cloud Computing" },
  { value: "devops", label: "DevOps" },
  { value: "cybersecurity", label: "Cybersecurity" },
  { value: "database", label: "Database" },
  { value: "design", label: "Design" },
  { value: "business", label: "Business" },
  { value: "marketing", label: "Marketing" },
  { value: "other", label: "Other" },
];

// Course levels
const COURSE_LEVELS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "all_levels", label: "All Levels" },
];

// Format file size for display
const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// Get file icon based on type
const getFileIcon = (mimeType) => {
  if (mimeType?.startsWith("video/")) {
    return <Video className="w-5 h-5 text-purple-500" />;
  }
  return <FileText className="w-5 h-5 text-blue-500" />;
};

// Validate file type
const isValidDocumentType = (file) => {
  const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
  return (
    ALLOWED_DOCUMENT_TYPES.includes(file.type) ||
    ALLOWED_DOCUMENT_EXTENSIONS.includes(extension)
  );
};

const isValidVideoType = (file) => {
  return ALLOWED_VIDEO_TYPES.includes(file.type);
};

const CourseCreate = ({ setActiveTab, editingCourse, setEditingCourse }) => {
  // Course basic info
  const [courseData, setCourseData] = useState({
    title: "",
    subtitle: "",
    description: "",
    category: "",
    level: "beginner",
    language: "en",
    visibility: "public",
  });

  // Sections state
  const [sections, setSections] = useState([]);
  const [expandedSections, setExpandedSections] = useState({});
  const [originalSectionIds, setOriginalSectionIds] = useState([]); // Track original sections for editing

  // Upload state
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadStatus, setUploadStatus] = useState("idle"); // idle, creating, success, error
  const [errorMessage, setErrorMessage] = useState("");
  const [validationErrors, setValidationErrors] = useState({});
  const [createdCourse, setCreatedCourse] = useState(null);

  const fileInputRefs = useRef({});
  const abortControllerRef = useRef(null);

  // Handle back navigation
  const handleBack = useCallback(() => {
    if (setEditingCourse) {
      setEditingCourse(null);
    }
    if (setActiveTab) {
      setActiveTab("courses");
    }
  }, [setActiveTab, setEditingCourse]);

  // Load editing course data
  useEffect(() => {
    if (editingCourse) {
      setCourseData({
        title: editingCourse.title || "",
        subtitle: editingCourse.subtitle || "",
        description: editingCourse.description || "",
        category: editingCourse.category || "",
        level: editingCourse.level || "beginner",
        language: editingCourse.language || "en",
        visibility: editingCourse.visibility || "private",
      });
      // Load sections if available
      if (editingCourse.sections) {
        setSections(editingCourse.sections);
        // Track original section IDs to detect deletions
        setOriginalSectionIds(editingCourse.sections.map(s => s.id));
      }
    } else {
      // Reset original section IDs when not editing
      setOriginalSectionIds([]);
    }
  }, [editingCourse]);

  // Validate course form
  const validateCourseForm = useCallback(() => {
    const errors = {};

    if (!courseData.title.trim()) {
      errors.title = "Course title is required";
    } else if (courseData.title.length > MAX_TITLE_LENGTH) {
      errors.title = `Title must be less than ${MAX_TITLE_LENGTH} characters`;
    }

    if (
      courseData.description &&
      courseData.description.length > MAX_DESCRIPTION_LENGTH
    ) {
      errors.description = `Description must be less than ${MAX_DESCRIPTION_LENGTH} characters`;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [courseData]);

  // Handle course input changes
  const handleCourseInputChange = useCallback((e) => {
    const { name, value } = e.target;
    setCourseData((prev) => ({ ...prev, [name]: value }));
    setValidationErrors((prev) => ({ ...prev, [name]: undefined }));
  }, []);

  // Add new section
  const addSection = useCallback(() => {
    const newSection = {
      id: `section-${Date.now()}`,
      title: `Section ${sections.length + 1}`,
      description: "",
      order: sections.length,
      contents: [],
    };
    setSections((prev) => [...prev, newSection]);
    setExpandedSections((prev) => ({ ...prev, [newSection.id]: true }));
  }, [sections.length]);

  // Update section
  const updateSection = useCallback((sectionId, updates) => {
    setSections((prev) =>
      prev.map((section) =>
        section.id === sectionId ? { ...section, ...updates } : section
      )
    );
  }, []);

  // Remove section
  const removeSection = useCallback((sectionId) => {
    setSections((prev) => prev.filter((section) => section.id !== sectionId));
    setExpandedSections((prev) => {
      const newState = { ...prev };
      delete newState[sectionId];
      return newState;
    });
  }, []);

  // Toggle section expand/collapse
  const toggleSection = useCallback((sectionId) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  }, []);

  // Add content to section
  const addContentToSection = useCallback((sectionId, file, type) => {
    const content = {
      id: `content-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      title: file.name.replace(/\.[^/.]+$/, ""),
      type,
      file,
      size: file.size,
      mimeType: file.type,
      uploadStatus: "pending",
      progress: 0,
    };

    setSections((prev) =>
      prev.map((section) =>
        section.id === sectionId
          ? { ...section, contents: [...section.contents, content] }
          : section
      )
    );
  }, []);

  // Remove content from section
  const removeContentFromSection = useCallback((sectionId, contentId) => {
    setSections((prev) =>
      prev.map((section) =>
        section.id === sectionId
          ? {
            ...section,
            contents: section.contents.filter((c) => c.id !== contentId),
          }
          : section
      )
    );
  }, []);

  // Update content title
  const updateContentTitle = useCallback((sectionId, contentId, title) => {
    setSections((prev) =>
      prev.map((section) =>
        section.id === sectionId
          ? {
            ...section,
            contents: section.contents.map((c) =>
              c.id === contentId ? { ...c, title } : c
            ),
          }
          : section
      )
    );
  }, []);

  // Handle file drop for section
  const handleFileDrop = useCallback(
    (sectionId, e) => {
      e.preventDefault();
      e.stopPropagation();

      const files = Array.from(e.dataTransfer?.files || []);
      files.forEach((file) => {
        if (isValidVideoType(file)) {
          if (file.size <= MAX_VIDEO_SIZE) {
            addContentToSection(sectionId, file, "video");
          } else {
            setErrorMessage(`Video file "${file.name}" exceeds 500MB limit`);
          }
        } else if (isValidDocumentType(file)) {
          if (file.size <= MAX_DOCUMENT_SIZE) {
            addContentToSection(sectionId, file, "document");
          } else {
            setErrorMessage(`Document "${file.name}" exceeds 5MB limit`);
          }
        } else {
          setErrorMessage(`File type not supported: ${file.name}`);
        }
      });
    },
    [addContentToSection]
  );

  // Handle file input change for section
  const handleFileInputChange = useCallback(
    (sectionId, e) => {
      const files = Array.from(e.target.files || []);
      files.forEach((file) => {
        if (isValidVideoType(file)) {
          if (file.size <= MAX_VIDEO_SIZE) {
            addContentToSection(sectionId, file, "video");
          } else {
            setErrorMessage(`Video file "${file.name}" exceeds 500MB limit`);
          }
        } else if (isValidDocumentType(file)) {
          if (file.size <= MAX_DOCUMENT_SIZE) {
            addContentToSection(sectionId, file, "document");
          } else {
            setErrorMessage(`Document "${file.name}" exceeds 5MB limit`);
          }
        } else {
          setErrorMessage(`File type not supported: ${file.name}`);
        }
      });
      // Reset input
      e.target.value = "";
    },
    [addContentToSection]
  );

  // Create or update course and upload content
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    if (!validateCourseForm()) {
      return;
    }

    setUploadStatus("creating");
    abortControllerRef.current = new AbortController();

    try {
      // Step 1: Create or update the course
      const coursePayload = {
        title: courseData.title.trim(),
        ...(courseData.subtitle && { subtitle: courseData.subtitle.trim() }),
        ...(courseData.description && {
          description: courseData.description.trim(),
        }),
        ...(courseData.category && { category: courseData.category }),
        level: courseData.level,
        language: courseData.language,
        visibility: courseData.visibility,
      };

      let course;
      if (editingCourse) {
        // Update existing course
        course = await facultyApi.updateCourse(editingCourse.id, coursePayload);
      } else {
        // Create new course
        course = await facultyApi.createCourse(coursePayload);
      }

      if (!course || !course.id) {
        throw new Error(editingCourse ? "Failed to update course - invalid response" : "Failed to create course - invalid response");
      }

      setCreatedCourse(course);

      // Step 2: Handle sections - different logic for edit vs create
      if (editingCourse) {
        // EDITING MODE: Update/Delete/Create sections as needed
        const currentSectionIds = sections.map(s => s.id);

        // Delete sections that were removed (in original but not in current)
        const sectionsToDelete = originalSectionIds.filter(
          id => !currentSectionIds.includes(id)
        );

        for (const sectionId of sectionsToDelete) {
          try {
            await facultyApi.deleteSection(sectionId);
          } catch (error) {
            console.error(`Failed to delete section: ${sectionId}`, error);
          }
        }

        // Process each current section
        for (const section of sections) {
          // Check if this is an existing section (UUID format) or new (section-timestamp format)
          const isExistingSection = originalSectionIds.includes(section.id);

          let targetSectionId;

          if (isExistingSection) {
            // Update existing section
            try {
              await facultyApi.updateSection(section.id, {
                title: section.title,
                description: section.description || undefined,
                order: section.order,
              });
              targetSectionId = section.id;
            } catch (error) {
              console.error(`Failed to update section: ${section.title}`, error);
              continue;
            }
          } else {
            // Create new section
            try {
              const sectionResponse = await facultyApi.addSection(course.id, {
                title: section.title,
                description: section.description || undefined,
                order: section.order,
              });

              if (!sectionResponse || !sectionResponse.id) {
                console.error(`Failed to create section: ${section.title}`);
                continue;
              }
              targetSectionId = sectionResponse.id;
            } catch (error) {
              console.error(`Failed to create section: ${section.title}`, error);
              continue;
            }
          }

          // Upload only new content (items with file property)
          for (const content of section.contents) {
            // Skip if no file (existing content)
            if (!content.file) continue;

            if (content.type === "video") {
              try {
                const videoFormData = new FormData();
                videoFormData.append("video", content.file);
                videoFormData.append("title", content.title);
                videoFormData.append("category", "lecture");
                videoFormData.append("visibility", "private");

                const videoResponse = await facultyApi.uploadVideo(
                  videoFormData,
                  (progress) => {
                    setUploadProgress((prev) => ({
                      ...prev,
                      [content.id]: progress,
                    }));
                  },
                  abortControllerRef.current?.signal
                );

                const videoId = videoResponse?.data?.id || videoResponse?.id;

                if (!videoId) {
                  throw new Error("Video upload succeeded but no video ID returned");
                }

                await facultyApi.addContent(targetSectionId, {
                  title: content.title,
                  videoId: videoId,
                });

                setSections((prev) =>
                  prev.map((s) =>
                    s.id === section.id
                      ? {
                        ...s,
                        contents: s.contents.map((c) =>
                          c.id === content.id
                            ? { ...c, uploadStatus: "success" }
                            : c
                        ),
                      }
                      : s
                  )
                );
              } catch (error) {
                console.error(`Failed to upload video: ${content.title}`, error);
                setSections((prev) =>
                  prev.map((s) =>
                    s.id === section.id
                      ? {
                        ...s,
                        contents: s.contents.map((c) =>
                          c.id === content.id
                            ? { ...c, uploadStatus: "error" }
                            : c
                        ),
                      }
                      : s
                  )
                );
              }
            } else if (content.type === "document") {
              try {
                const formData = new FormData();
                formData.append("file", content.file);
                formData.append("title", content.title);

                await facultyApi.uploadDocument(
                  targetSectionId,
                  formData,
                  (progress) => {
                    setUploadProgress((prev) => ({
                      ...prev,
                      [content.id]: progress,
                    }));
                  },
                  abortControllerRef.current?.signal
                );

                setSections((prev) =>
                  prev.map((s) =>
                    s.id === section.id
                      ? {
                        ...s,
                        contents: s.contents.map((c) =>
                          c.id === content.id
                            ? { ...c, uploadStatus: "success" }
                            : c
                        ),
                      }
                      : s
                  )
                );
              } catch (error) {
                console.error(`Failed to upload document: ${content.title}`, error);
                setSections((prev) =>
                  prev.map((s) =>
                    s.id === section.id
                      ? {
                        ...s,
                        contents: s.contents.map((c) =>
                          c.id === content.id
                            ? { ...c, uploadStatus: "error" }
                            : c
                        ),
                      }
                      : s
                  )
                );
              }
            }
          }
        }
      } else {
        // CREATE MODE: Create all sections and upload content
        for (const section of sections) {
          const sectionResponse = await facultyApi.addSection(course.id, {
            title: section.title,
            description: section.description || undefined,
            order: section.order,
          });

          const createdSection = sectionResponse;

          if (!createdSection || !createdSection.id) {
            console.error(`Failed to create section: ${section.title}`);
            continue;
          }

          for (const content of section.contents) {
            if (content.type === "video") {
              try {
                const videoFormData = new FormData();
                videoFormData.append("video", content.file);
                videoFormData.append("title", content.title);
                videoFormData.append("category", "lecture");
                videoFormData.append("visibility", "private");

                const videoResponse = await facultyApi.uploadVideo(
                  videoFormData,
                  (progress) => {
                    setUploadProgress((prev) => ({
                      ...prev,
                      [content.id]: progress,
                    }));
                  },
                  abortControllerRef.current?.signal
                );

                const videoId = videoResponse?.data?.id || videoResponse?.id;

                if (!videoId) {
                  throw new Error("Video upload succeeded but no video ID returned");
                }

                await facultyApi.addContent(createdSection.id, {
                  title: content.title,
                  videoId: videoId,
                });

                setSections((prev) =>
                  prev.map((s) =>
                    s.id === section.id
                      ? {
                        ...s,
                        contents: s.contents.map((c) =>
                          c.id === content.id
                            ? { ...c, uploadStatus: "success" }
                            : c
                        ),
                      }
                      : s
                  )
                );
              } catch (error) {
                console.error(`Failed to upload video: ${content.title}`, error);
                setSections((prev) =>
                  prev.map((s) =>
                    s.id === section.id
                      ? {
                        ...s,
                        contents: s.contents.map((c) =>
                          c.id === content.id
                            ? { ...c, uploadStatus: "error" }
                            : c
                        ),
                      }
                      : s
                  )
                );
              }
            } else if (content.type === "document") {
              try {
                const formData = new FormData();
                formData.append("file", content.file);
                formData.append("title", content.title);

                await facultyApi.uploadDocument(
                  createdSection.id,
                  formData,
                  (progress) => {
                    setUploadProgress((prev) => ({
                      ...prev,
                      [content.id]: progress,
                    }));
                  },
                  abortControllerRef.current?.signal
                );

                setSections((prev) =>
                  prev.map((s) =>
                    s.id === section.id
                      ? {
                        ...s,
                        contents: s.contents.map((c) =>
                          c.id === content.id
                            ? { ...c, uploadStatus: "success" }
                            : c
                        ),
                      }
                      : s
                  )
                );
              } catch (error) {
                console.error(`Failed to upload document: ${content.title}`, error);
                setSections((prev) =>
                  prev.map((s) =>
                    s.id === section.id
                      ? {
                        ...s,
                        contents: s.contents.map((c) =>
                          c.id === content.id
                            ? { ...c, uploadStatus: "error" }
                            : c
                        ),
                      }
                      : s
                  )
                );
              }
            }
          }
        }
      }

      setUploadStatus("success");
    } catch (error) {
      console.error("Course creation error:", error);
      setErrorMessage(error.message || "Failed to create course");
      setUploadStatus("error");
    }
  };

  // Reset form
  const resetForm = useCallback(() => {
    setCourseData({
      title: "",
      subtitle: "",
      description: "",
      category: "",
      level: "beginner",
      language: "en",
      visibility: "private",
    });
    setSections([]);
    setExpandedSections({});
    setUploadProgress({});
    setUploadStatus("idle");
    setErrorMessage("");
    setValidationErrors({});
    setCreatedCourse(null);
    if (setEditingCourse) {
      setEditingCourse(null);
    }
  }, [setEditingCourse]);

  // Render success state
  if (uploadStatus === "success") {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {editingCourse ? "Course Updated Successfully!" : "Course Created Successfully!"}
          </h2>
          <p className="text-gray-600 mb-6">
            Your course "{createdCourse?.title}" has been {editingCourse ? "updated" : "created"}.
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={resetForm}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Create Another Course
            </button>
            <button
              onClick={handleBack}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Back to Courses
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header with back button */}
      <div className="mb-6">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Courses</span>
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          {editingCourse ? "Edit Course" : "Create New Course"}
        </h1>
        <p className="text-gray-600 mt-1">
          {editingCourse
            ? "Update your course details and content"
            : "Fill in the course details and add your content"}
        </p>
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-red-600 text-sm">{errorMessage}</p>
          </div>
          <button
            onClick={() => setErrorMessage("")}
            className="ml-auto text-red-500 hover:text-red-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Course Basic Info */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Course Information
          </h2>

          <div className="space-y-4">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Course Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={courseData.title}
                onChange={handleCourseInputChange}
                placeholder="Enter course title"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${validationErrors.title ? "border-red-500" : "border-gray-300"
                  }`}
              />
              {validationErrors.title && (
                <p className="mt-1 text-sm text-red-500">
                  {validationErrors.title}
                </p>
              )}
            </div>

            {/* Subtitle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subtitle
              </label>
              <input
                type="text"
                name="subtitle"
                value={courseData.subtitle}
                onChange={handleCourseInputChange}
                placeholder="A brief subtitle for your course"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                name="description"
                value={courseData.description}
                onChange={handleCourseInputChange}
                placeholder="Describe what students will learn..."
                rows={4}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${validationErrors.description
                  ? "border-red-500"
                  : "border-gray-300"
                  }`}
              />
              {validationErrors.description && (
                <p className="mt-1 text-sm text-red-500">
                  {validationErrors.description}
                </p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                {courseData.description.length}/{MAX_DESCRIPTION_LENGTH}{" "}
                characters
              </p>
            </div>

            {/* Category & Level Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  name="category"
                  value={courseData.category}
                  onChange={handleCourseInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {COURSE_CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Level
                </label>
                <select
                  name="level"
                  value={courseData.level}
                  onChange={handleCourseInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {COURSE_LEVELS.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Visibility */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Visibility
              </label>
              <select
                name="visibility"
                value={courseData.visibility}
                onChange={handleCourseInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="unlisted">Unlisted (Accessible via link)</option>
                <option value="private">
                  Private (Enrolled students only)
                </option>
                <option value="public">Public (Everyone can see)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Course Sections */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Course Content
            </h2>
            <button
              type="button"
              onClick={addSection}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Section
            </button>
          </div>

          {sections.length === 0 ? (
            <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 mb-2">No sections added yet</p>
              <p className="text-sm text-gray-500">
                Click "Add Section" to start building your course
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {sections.map((section, index) => (
                <div
                  key={section.id}
                  className="border border-gray-200 rounded-lg overflow-hidden"
                >
                  {/* Section Header */}
                  <div className="bg-gray-50 px-4 py-3 flex items-center gap-3">
                    <GripVertical className="w-5 h-5 text-gray-400 cursor-move" />
                    <button
                      type="button"
                      onClick={() => toggleSection(section.id)}
                      className="text-gray-600 hover:text-gray-800"
                    >
                      {expandedSections[section.id] ? (
                        <ChevronUp className="w-5 h-5" />
                      ) : (
                        <ChevronDown className="w-5 h-5" />
                      )}
                    </button>
                    <input
                      type="text"
                      value={section.title}
                      onChange={(e) =>
                        updateSection(section.id, { title: e.target.value })
                      }
                      className="flex-1 px-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="Section title"
                    />
                    <span className="text-sm text-gray-500">
                      {section.contents.length} item(s)
                    </span>
                    <button
                      type="button"
                      onClick={() => removeSection(section.id)}
                      className="text-red-500 hover:text-red-700 p-1"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Section Content */}
                  {expandedSections[section.id] && (
                    <div className="p-4">
                      {/* Section Description */}
                      <textarea
                        value={section.description}
                        onChange={(e) =>
                          updateSection(section.id, {
                            description: e.target.value,
                          })
                        }
                        placeholder="Section description (optional)"
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 mb-4"
                      />

                      {/* Content Items */}
                      {section.contents.length > 0 && (
                        <div className="space-y-2 mb-4">
                          {section.contents.map((content) => (
                            <div
                              key={content.id}
                              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                            >
                              {getFileIcon(content.mimeType)}
                              <input
                                type="text"
                                value={content.title}
                                onChange={(e) =>
                                  updateContentTitle(
                                    section.id,
                                    content.id,
                                    e.target.value
                                  )
                                }
                                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                              />
                              <span className="text-xs text-gray-500">
                                {formatFileSize(content.size)}
                              </span>
                              {uploadProgress[content.id] !== undefined && (
                                <div className="w-20 bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-indigo-600 h-2 rounded-full transition-all"
                                    style={{
                                      width: `${uploadProgress[content.id]}%`,
                                    }}
                                  />
                                </div>
                              )}
                              {content.uploadStatus === "success" && (
                                <CheckCircle className="w-5 h-5 text-green-500" />
                              )}
                              {content.uploadStatus === "error" && (
                                <AlertCircle className="w-5 h-5 text-red-500" />
                              )}
                              <button
                                type="button"
                                onClick={() =>
                                  removeContentFromSection(
                                    section.id,
                                    content.id
                                  )
                                }
                                className="text-red-500 hover:text-red-700 p-1"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Drop Zone */}
                      <div
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => handleFileDrop(section.id, e)}
                        className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-500 transition-colors"
                      >
                        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600 mb-2">
                          Drag and drop files here, or{" "}
                          <label className="text-indigo-600 hover:text-indigo-700 cursor-pointer">
                            browse
                            <input
                              type="file"
                              multiple
                              accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.mp4,.webm,.ogg,.mov"
                              onChange={(e) =>
                                handleFileInputChange(section.id, e)
                              }
                              className="hidden"
                              ref={(el) =>
                                (fileInputRefs.current[section.id] = el)
                              }
                            />
                          </label>
                        </p>
                        <p className="text-xs text-gray-500">
                          Videos up to 500MB, Documents up to 5MB (PDF, Word,
                          PPT, Excel, TXT)
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={resetForm}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={uploadStatus === "creating"}
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploadStatus === "creating" ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {editingCourse ? "Saving..." : "Creating..."}
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                {editingCourse ? "Save Changes" : "Create Course"}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CourseCreate;
