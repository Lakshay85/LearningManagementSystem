import React from "react";
import VideoAnalytics from "./VideoAnalytics";
import CourseAnalytics from "./CourseAnalytics";

const Analytics = () => {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Content Analytics</h1>
                <p className="text-gray-500 mt-1">
                    Detailed breakdown of your content visibility and updates
                </p>
            </div>

            <VideoAnalytics />
            <CourseAnalytics />
        </div>
    );
};

export default Analytics;
