import React, { useState, useEffect } from "react";
import { BookOpen, Clock, Calendar } from "lucide-react";
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
} from "chart.js";
import { Doughnut, Bar } from "react-chartjs-2";
import facultyApi from "../../../utils/facultyApi";

ChartJS.register(
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title
);

const CourseAnalytics = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const response = await facultyApi.getCourseAnalyticsDetails();
            setData(response.data);
        } catch (error) {
            console.error("Failed to fetch course analytics:", error);
        } finally {
            setLoading(false);
        }
    };

    const getChartData = () => {
        if (!data) return null;

        // Doughnut Data (Status)
        const statusData = {
            labels: ["Published", "Draft"],
            datasets: [
                {
                    data: [data.publishedCourses.length, data.draftCourses.length],
                    backgroundColor: ["#10b981", "#f59e0b"],
                    borderColor: ["#059669", "#d97706"],
                    borderWidth: 1,
                },
            ],
        };

        // Bar Data (Monthly Creation)
        const allCourses = [...data.publishedCourses, ...data.draftCourses];
        const months = {};
        const today = new Date();

        // Initialize last 6 months
        for (let i = 5; i >= 0; i--) {
            const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
            const monthYear = d.toLocaleString('default', { month: 'short', year: 'numeric' });
            months[monthYear] = 0;
        }

        allCourses.forEach(course => {
            const d = new Date(course.createdAt);
            const monthYear = d.toLocaleString('default', { month: 'short', year: 'numeric' });
            if (monthYear in months) {
                months[monthYear]++;
            }
        });

        const timelineData = {
            labels: Object.keys(months),
            datasets: [
                {
                    label: "Courses Created",
                    data: Object.values(months),
                    backgroundColor: "#10b981",
                    borderRadius: 4,
                }
            ]
        };

        return { statusData, timelineData };
    };

    if (loading) {
        return <div className="p-8 text-center text-gray-500">Loading course analytics...</div>;
    }

    if (!data) return null;

    const chartData = getChartData();

    return (
        <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                        <BookOpen className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-gray-900">Course Analytics</h2>
                        <p className="text-sm text-gray-500">Total Courses: {data.totalCourses}</p>
                    </div>
                </div>

                {/* Charts Section */}
                <div className="grid md:grid-cols-2 gap-8 mb-8">
                    <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm flex flex-col items-center">
                        <h3 className="text-sm font-medium text-gray-700 mb-4">Content Status</h3>
                        <div className="w-full max-w-[250px]">
                            <Doughnut data={chartData.statusData} options={{ maintainAspectRatio: true, plugins: { legend: { position: 'bottom' } } }} />
                        </div>
                    </div>
                    <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
                        <h3 className="text-sm font-medium text-gray-700 mb-4">Creation Trends (Last 6 Months)</h3>
                        <div className="w-full h-[250px]">
                            <Bar data={chartData.timelineData} options={{ maintainAspectRatio: false, responsive: true }} />
                        </div>
                    </div>
                </div>


            </div>
        </div>
    );
};

export default CourseAnalytics;
