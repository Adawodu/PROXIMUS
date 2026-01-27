import { useResumes } from '../hooks/useResumes';
import { ResumeList } from '../components/resumes/ResumeList';
import { ResumeUpload } from '../components/resumes/ResumeUpload';

export function Resumes() {
  const { resumes, loading, refetch } = useResumes();

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Resumes</h2>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ResumeList resumes={resumes} loading={loading} onChanged={refetch} />
        </div>
        <div>
          <ResumeUpload onUploaded={refetch} />
        </div>
      </div>
    </div>
  );
}
