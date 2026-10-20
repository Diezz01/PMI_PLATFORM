import styles from './css/App.module.css'
import logoUnicam from './assets/Logo_unicam-removebg-preview.png'

function App() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.brand}>
            <img
                src={logoUnicam}
                alt="University of Camerino"
                className={styles.unicamLogo}
              />

            <div>
              <p className={styles.brandName}>UNICAM PMI Platform</p>
              <p className={styles.brandDescription}>
                Estimation of the post-mortem interval
              </p>
            </div>
          </div>

          <span className={styles.context}>Forensic Medicine</span>
        </div>
      </header>
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <p className={styles.footerBrand}>UNICAM PMI Platform</p>
          <p className={styles.footerDescription}>
            Master Thesis Project · Computer Science Department
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App