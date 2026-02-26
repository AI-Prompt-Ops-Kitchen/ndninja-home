import { getSession } from '@/lib/session';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { report_type = 'daily' } = await request.json();

    // TODO: Implement local email sending (e.g., via nodemailer)
    return NextResponse.json({
      message: `Report type "${report_type}" requested — email sending not yet configured for local mode.`,
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
