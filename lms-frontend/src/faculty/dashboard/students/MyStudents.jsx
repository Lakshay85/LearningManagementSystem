import React, { useState, useEffect } from "react";
import { Search } from "lucide-react";
import facultyApi from "../../../utils/facultyApi";
import StudentTable from "./StudentTable";

const MyStudents = () => {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");

    useEffect(() => {
        fetchStudents();
    }, []);

    const fetchStudents = async () => {
        try {
            const response = await facultyApi.getFacultyStudents();
            setStudents(response);
        } catch (error) {
            console.error("Failed to fetch students:", error);
        } finally {
            setLoading(false);
        }
    };

    const filteredStudents = (students || []).filter((student) => {
        const searchLower = searchTerm.toLowerCase();
        const fullName = `${student.firstName} ${student.lastName}`.toLowerCase();
        const email = student.email.toLowerCase();
        const courseTitle = student.course.title.toLowerCase();

        return (
            fullName.includes(searchLower) ||
            email.includes(searchLower) ||
            courseTitle.includes(searchLower)
        );
    });

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Enrolled Students</h1>
                    <p className="text-gray-500 mt-1">
                        Manage and view progress of students enrolled in your courses
                    </p>
                </div>

                <div className="relative w-full md:w-72">
                    <input
                        type="text"
                        placeholder="Search students..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all duration-200"
                    />
                    <Search className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" />
                </div>
            </div>

            <StudentTable students={filteredStudents} loading={loading} />
        </div>
    );
};

export default MyStudents;
