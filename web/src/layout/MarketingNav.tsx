import { NavLink } from 'react-router-dom'
import { brand } from '../brand'

const links = [
  ['/desk', 'Product'],
  ['/games?league=NFL', 'NFL'],
  ['/games?league=CFB', 'College Football'],
  ['/models', 'Models'],
  ['/about', 'About'],
  ['/research', 'Research'],
  ['/pricing', 'Pricing'],
] as const

export function BrandLockup({ compact = false }: { compact?: boolean }) {
  return (
    <span className={compact ? 'brand brand-compact' : 'brand'}>
      <img className="brand-icon" src={brand.icon} alt="" width={32} height={32} />
      <img
        className="brand-wordmark"
        src={brand.wordmark}
        alt="BlueChipWager"
        height={compact ? 26 : 32}
      />
    </span>
  )
}

export function MarketingNav() {
  return (
    <header className="mnav">
      <NavLink to="/" aria-label="BlueChipWager home">
        <BrandLockup />
      </NavLink>
      <nav>
        {links.map(([to, label]) => (
          <NavLink key={to} to={to}>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="mnav-actions">
        <span className="link-quiet">Sign In</span>
        <NavLink className="btn btn-primary" to="/desk">
          Start Free
        </NavLink>
      </div>
    </header>
  )
}
