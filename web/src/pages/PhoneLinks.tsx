import { usePhoneLinks } from '../hooks/usePhoneLinks';
import { useResumes } from '../hooks/useResumes';
import { PhoneLinkList } from '../components/phone-links/PhoneLinkList';
import { PhoneLinkCreate } from '../components/phone-links/PhoneLinkCreate';

export function PhoneLinks() {
  const { links, loading, refetch } = usePhoneLinks();
  const { resumes } = useResumes();

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Phone Links</h2>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <PhoneLinkList links={links} loading={loading} onChanged={refetch} />
        </div>
        <div>
          <PhoneLinkCreate resumes={resumes} onCreated={refetch} />
        </div>
      </div>
    </div>
  );
}
