import React from "react";
import { User, Video, FileText, Calendar } from "lucide-react";

const StudentTable = ({ students, loading }) => {
    if (loading) {
        return (
            <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-8 text-center text-gray-500">Loading students...</div>
            </div>
        );
    }

    if (!students || students.length === 0) {
        return (
            <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-12 flex flex-col items-center justify-center text-gray-500">
                    <User className="w-12 h-12 text-gray-300 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900">No Students Found</h3>
                    <p className="text-sm">You usually don't have any students enrolled in your courses yet.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="bg-gray-50 border-b border-gray-100">
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                Student
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                Enrolled Course
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                Progress
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                Joined Date
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {students.map((student, index) => (
                            <tr
                                key={`${student.id}-${student.course.id}-${index}`}
                                className="hover:bg-gray-50 transition-colors duration-150"
                            >
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center gap-3">
                                        {student.profilePicture ? (
                                            <img
                                                src={student.profilePicture}
                                                alt={`${student.firstName} ${student.lastName}`}
                                                className="w-10 h-10 rounded-full object-cover border border-gray-200"
                                            />
                                        ) : (
                                            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 font-medium text-sm">
                                                {student.firstName?.[0]}{student.lastName?.[0]}
                                            </div>
                                        )}
                                        <div>
                                            <div className="text-sm font-medium text-gray-900">
                                                {student.firstName} {student.lastName}
                                            </div>
                                            <div className="text-xs text-gray-500">{student.email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm text-gray-900 font-medium">{student.course.title}</div>
                                    <div className="text-xs text-gray-500 flex items-center gap-2 mt-0.5">
                                        <span className="flex items-center gap-1">
                                            <Video className="w-3 h-3" /> {student.course.totalVideos || 0} Videos
                                        </span>
                                        <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
                                        <span className="flex items-center gap-1">
                                            <FileText className="w-3 h-3" /> {student.course.totalDocuments || 0} Docs
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center gap-3">
                                        <div className="flex-1 w-24 bg-gray-100 rounded-full h-2">
                                            <div
                                                className="bg-emerald-500 h-2 rounded-full"
                                                style={{ width: `${student.progress || 0}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-sm text-gray-600 font-medium">
                                            {Math.round(student.progress || 0)}%
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center gap-2 text-sm text-gray-500">
                                        <Calendar className="w-4 h-4 text-gray-400" />
                                        {new Date(student.enrolledAt).toLocaleDateString()}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default StudentTable;
