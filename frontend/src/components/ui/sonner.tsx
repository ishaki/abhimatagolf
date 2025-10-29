import { Toaster as Sonner } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="light"
      className="toaster group"
      position="top-right"
      richColors={true}
      closeButton={true}
      expand={false}
      duration={4000}
      visibleToasts={5}
      toastOptions={{
        style: {
          background: 'white',
          border: '1px solid #e5e7eb',
          fontSize: '14px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          padding: '16px',
          borderRadius: '8px',
        },
        className: 'toast-item',
        classNames: {
          error: 'toast-error',
          success: 'toast-success',
          warning: 'toast-warning',
          info: 'toast-info',
          toast: 'sonner-toast',
          title: 'sonner-toast-title',
          description: 'sonner-toast-description',
          actionButton: 'sonner-toast-action',
          cancelButton: 'sonner-toast-cancel',
          closeButton: 'sonner-toast-close',
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
