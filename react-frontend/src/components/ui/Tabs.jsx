import { cn } from '../../utils/cn';
import { useState } from 'react';

export default function Tabs({
  tabs = [],
  onChange,
  defaultValue,
  className,
  ...props
}) {
  const [activeTab, setActiveTab] = useState(defaultValue || (tabs[0]?.value || ''));

  const handleTabChange = (value) => {
    setActiveTab(value);
    onChange && onChange(value);
  };

  return (
    <div className={cn('w-full', className)} {...props}>
      {/* Tab List */}
      <div className="flex gap-2 border-b border-slate-200 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleTabChange(tab.value)}
            className={cn(
              'px-4 py-3 text-sm font-medium transition-all duration-200',
              'border-b-2 border-transparent -mb-[2px]',
              'hover:text-purple-600',
              activeTab === tab.value
                ? 'text-purple-600 border-b-purple-600'
                : 'text-slate-600'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tabs.map((tab) => (
        <div
          key={tab.value}
          className={cn('animate-fade-in', activeTab !== tab.value && 'hidden')}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}
